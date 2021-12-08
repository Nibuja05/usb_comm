/*
 * ffs-test.c -- user mode filesystem api for usb composite function
 *
 * Copyright (C) 2010 Samsung Electronics
 *                    Author: Michal Nazarewicz <mina86@mina86.com>
 * Copyright 2019 Collabora Ltd
 *                    Author: Andrzej Pietrasiewicz <andrzej.p@collabora.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

/* $(CROSS_COMPILE)cc -Wall -Wextra -g -o ffs-test ffs-test.c -lpthread */

#define _DEFAULT_SOURCE /* for endian.h */

#include <endian.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
// #include <tools/le_byteshift.h>
#include "../include/tools/le_byteshift.h"
#include <systemd/sd-daemon.h>

#include "../../include/uapi/linux/usb/functionfs.h"

/******************** Little Endian Handling ********************************/

/*
 * cpu_to_le16/32 are used when initializing structures, a context where a
 * function call is not allowed. To solve this, we code cpu_to_le16/32 in a way
 * that allows them to be used when initializing structures.
 */

#if __BYTE_ORDER == __LITTLE_ENDIAN
#define cpu_to_le16(x)  (x)
#define cpu_to_le32(x)  (x)
#else
#define cpu_to_le16(x)  ((((x) >> 8) & 0xffu) | (((x) & 0xffu) << 8))
#define cpu_to_le32(x)  \
	((((x) & 0xff000000u) >> 24) | (((x) & 0x00ff0000u) >>  8) | \
	(((x) & 0x0000ff00u) <<  8) | (((x) & 0x000000ffu) << 24))
#endif

#define le32_to_cpu(x)  le32toh(x)
#define le16_to_cpu(x)  le16toh(x)

/******************** Messages and Errors ***********************************/

static void msg(const char *fmt, ...)
{
	int _errno = errno;
	va_list ap;

	fprintf(stderr, "%s: ", "ffs-test");
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);

	if (fmt[strlen(fmt) - 1] != '\n') {
		char buffer[128];
		strerror_r(_errno, buffer, sizeof(buffer));
		fprintf(stderr, ": (-%d) %s\n", _errno, buffer);
	}

	fflush(stderr);
}

#define die_on(cond, ...) do { \
	if (cond) { \
		msg(__VA_ARGS__); \
		exit(1); \
	} \
	} while (0)


/******************** Files and Threads Handling ****************************/

static ssize_t ep0_consume(int fd, const void *buf, size_t nbytes);

struct thread {
	const char *const tname;
	size_t buf_size;

	ssize_t (*in)(int, void *, size_t);
	const char *const in_name;

	ssize_t (*out)(int, const void *, size_t);
	const char *const out_name;

	int read_fd, write_fd;
	pthread_t id;
	void *buf;
	ssize_t status;
};

static char ep0_buf[4 * sizeof(struct usb_functionfs_event)];
static char ep1_2_buf[8 * 1024];

static struct thread ep0 = {
	"ep0", sizeof(ep0_buf),
	read, "ep0",
	ep0_consume, "<consume>",
	0, 0, 0, ep0_buf, 0
};

static struct thread ep1_2 = {
	"ep1_2", sizeof(ep1_2_buf),
	read, "ep2",
	write, "ep1",
	0, 0, 0, ep1_2_buf, 0
};

static void fifo_status(int fd, const char *tname)
{
	int ret;

	ret = ioctl(fd, FUNCTIONFS_FIFO_STATUS);
	if (ret < 0) {
		/* ENODEV reported after disconnect */
		if (errno != ENODEV)
			msg("%s: get fifo status", tname);
	} else if (ret) {
		msg("%s: unclaimed = %d\n", tname, ret);
		if (ioctl(fd, FUNCTIONFS_FIFO_FLUSH) < 0)
			msg("%s: fifo flush", tname);
	}
}

static void cleanup_thread(void *arg)
{
	struct thread *t = arg;
	int read_fd, write_fd;

	read_fd = t->read_fd;
	write_fd = t->write_fd;
	if (t->read_fd < 0 && t->write_fd < 0)
		return;
	t->read_fd = t->write_fd = -1;

	/* test the FIFO ioctls (non-ep0 code paths) */
	if (t == &ep1_2) {
		fifo_status(read_fd, t->tname);
		fifo_status(write_fd, t->tname);
		if (close(write_fd) < 0)
			msg("%s: close", t->tname);
	}

	if (close(read_fd) < 0)
		msg("%s: close", t->tname);
}

static void *start_helper(void *arg)
{
	const char *name, *op;
	struct thread *t = arg;
	ssize_t ret;

	msg("%s: starts\n", t->tname);

	pthread_cleanup_push(cleanup_thread, arg);

	for (;;) {
		pthread_testcancel();

		ret = t->in(t->read_fd, t->buf, t->buf_size);
		if (ret > 0) {
			ret = t->out(t->write_fd, t->buf, ret);
			name = t->out_name;
			op = "write";
		} else {
			name = t->in_name;
			op = "read";
		}

		if (ret > 0) {
			/* nop */
		} else if (!ret) {
			msg("%s: %s: EOF", name, op);
			break;
		} else if (errno == EINTR || errno == EAGAIN) {
			msg("%s: %s", name, op);
		} else {
			msg("%s: %s", name, op);
			break;
		}
	}

	pthread_cleanup_pop(1);

	t->status = ret;
	msg("%s: ends\n", t->tname);
	return NULL;
}

/******************** Endpoints routines ************************************/

static void handle_setup(const struct usb_ctrlrequest *setup)
{
	printf("bRequestType = %d\n", setup->bRequestType);
	printf("bRequest     = %d\n", setup->bRequest);
	printf("wValue       = %d\n", le16_to_cpu(setup->wValue));
	printf("wIndex       = %d\n", le16_to_cpu(setup->wIndex));
	printf("wLength      = %d\n", le16_to_cpu(setup->wLength));
}

static ssize_t
ep0_consume(int ignore, const void *buf, size_t nbytes)
{
	static const char *const names[] = {
		[FUNCTIONFS_BIND] = "BIND",
		[FUNCTIONFS_UNBIND] = "UNBIND",
		[FUNCTIONFS_ENABLE] = "ENABLE",
		[FUNCTIONFS_DISABLE] = "DISABLE",
		[FUNCTIONFS_SETUP] = "SETUP",
		[FUNCTIONFS_SUSPEND] = "SUSPEND",
		[FUNCTIONFS_RESUME] = "RESUME",
	};

	const struct usb_functionfs_event *event = buf;
	size_t n;

	(void)ignore;

	for (n = nbytes / sizeof(*event); n; --n, ++event)
		switch (event->type) {
		case FUNCTIONFS_BIND:
		case FUNCTIONFS_UNBIND:
		case FUNCTIONFS_ENABLE:
		case FUNCTIONFS_DISABLE:
		case FUNCTIONFS_SETUP:
		case FUNCTIONFS_SUSPEND:
		case FUNCTIONFS_RESUME:
			printf("Event %s\n", names[event->type]);
			if (event->type == FUNCTIONFS_SETUP)
				handle_setup(&event->u.setup);
			break;

		default:
			printf("Event %03u (unknown)\n", event->type);
		}

	return nbytes;
}

/******************** Main **************************************************/

int main(void)
{
	ssize_t ret;

	die_on(sd_listen_fds(0) != 3, "Cannot inherit descriptors from systemd");

	/* ep0 */
	ep0.write_fd = SD_LISTEN_FDS_START + 0;
	ep0.read_fd = ep0.write_fd;

	/* ep1 and ep2 */
	ep1_2.write_fd = SD_LISTEN_FDS_START + 1;
	ep1_2.read_fd = SD_LISTEN_FDS_START + 2;

	/* spawn the ep1_2 thread */
	ret = pthread_create(&ep1_2.id, NULL, start_helper, &ep1_2);
	die_on(ret < 0, "pthread_create(%s)", ep1_2.tname);

	/* main thread */
	start_helper(&ep0);

	/* wait for ep1_2 thread */
	ret = pthread_join(ep1_2.id, NULL);
	die_on(ret < 0, "%s: joining thread", ep1_2.tname);

	return 0;
}
