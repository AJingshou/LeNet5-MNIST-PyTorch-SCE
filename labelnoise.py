import os
import sys
if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle

import numpy as np

import torch
import torchvision.datasets as datasets

# 构造包含标签噪声的MNIST数据集

class MNISTNoisyLabels(datasets.MNIST):
    """MNIST Dataset with noisy labels.
    Args:
        noise_type (string): Noise type (default: 'symmetric').
            The value is either 'symmetric' or 'asymmetric'.
        noise_rate (float): Probability of label corruption (default: 0.0).
        seed (int): Random seed (default: 12345).
        
    This is a subclass of the `MNIST` Dataset.
    """

    def __init__(self,
                 noise_type='symmetric',
                 noise_rate=0.0,
                 seed=12345,
                 **kwargs):
        super(MNISTNoisyLabels, self).__init__(**kwargs)
        self.seed = seed
        self.num_classes = 10
        self.flip_pairs = np.asarray([[9, 1], [2, 0], [4, 7], [3, 5], [5, 3]])

        if noise_rate > 0:
            if noise_type == 'symmetric':
                self.symmetric_noise(noise_rate)
            elif noise_type == 'asymmetric':
                self.asymmetric_noise(noise_rate)
            else:
                raise ValueError(
                    'expected noise_type is either symmetric or asymmetric '
                    '(got {})'.format(noise_type))

    def symmetric_noise(self, noise_rate):
        """Insert symmetric noise.
        For all classes, ground truth labels are replaced with uniform random
        classes.
        """
        np.random.seed(self.seed)
        targets = np.array(self.targets)
        #print('target:{}'.format(targets))
        mask = np.random.rand(len(targets)) <= noise_rate
        rnd_targets = np.random.choice(self.num_classes, mask.sum())
        targets[mask] = rnd_targets
        targets = [int(target) for target in targets]
        #print('target:{}'.format(targets))
        #('target:{}'.format(targets))
        self.targets = targets

    def asymmetric_noise(self, noise_rate):
        """Insert asymmetric noise.
        Ground truth labels are flipped by mimicking real mistakes between
        similar classes. Following `Making Deep Neural Networks Robust to Label Noise: a Loss Correction Approach`_, 
        ground truth labels are replaced with
        
        * truck -> automobile,
        * bird -> airplane,
        * deer -> horse
        * cat -> dog
        * dog -> cat
        .. _Making Deep Neural Networks Robust to Label Noise: a Loss Correction Approach
            https://arxiv.org/abs/1609.03683
        """
        np.random.seed(self.seed)
        targets = np.array(self.targets)
        for i, target in enumerate(targets):
            if target in self.flip_pairs[:, 0]:
                if np.random.uniform(0, 1) <= noise_rate:
                    idx = int(np.where(self.flip_pairs[:, 0] == target)[0])
                    targets[i] = self.flip_pairs[idx, 1]
        targets = [int(x) for x in targets]
        self.targets = targets

    def T(self, noise_type, noise_rate):
        if noise_type == 'symmetric':
            T = (torch.eye(self.num_classes) * (1 - noise_rate) +
                 (torch.ones([self.num_classes, self.num_classes]) /
                  self.num_classes * noise_rate))
        elif noise_type == 'asymmetric':
            T = torch.eye(self.num_classes)
            for i, j in self.flip_pairs:
                T[i, i] = 1 - noise_rate
                T[i, j] = noise_rate
        return T
