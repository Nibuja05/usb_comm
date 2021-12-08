import numpy as np
import matplotlib.pyplot as plt

np.random.seed(123)

weight_pop = np.random.randint(100, 240, size=500000)
print(weight_pop)

print(np.mean(weight_pop))

print(np.std(weight_pop))

weight_sample = np.random.choice(weight_pop, size=1000)

sample_mean = np.mean(weight_sample)
print(sample_mean)

sample_std = np.std(weight_sample)
print(sample_std)

boot_means = []
for _ in range(10000):
    boot_sample = np.random.choice(weight_sample, replace=True, size=1000)
    boot_mean = np.mean(boot_sample)
    boot_means.append(boot_mean)

boot_means_np = np.array(boot_means)

print(boot_means_np)

boot_means = np.mean(boot_means_np)
print(boot_means)

print(np.mean(weight_pop))

boot_std = np.std(boot_means_np)
print(boot_std)

print(np.percentile(boot_means_np, [2.5, 98.5]))

plt.hist(boot_means_np, alpha=1)
plt.axvline(np.percentile(boot_means_np, 2.5), color="red", linewidth=2)
plt.axvline(np.percentile(boot_means_np, 97.5), color="red", linewidth=2)

plt.show()
