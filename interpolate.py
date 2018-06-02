
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.optim.lr_scheduler import ExponentialLR
from torchvision import datasets, transforms
from torch.autograd import Variable
import model
import os
import numpy as np

import scipy.misc
from glob import glob
import imageio
from skimage.transform import resize

parser = argparse.ArgumentParser()
parser.add_argument('--batch_size', type=int, default=32)
parser.add_argument('--checkpoint_dir', type=str, default='checkpoints')
parser.add_argument('--load', type=str)


parser.add_argument('--attention', action='store_true')

args = parser.parse_args()

num_classes = 10
Z_dim = 128
generator = model.Generator(Z_dim).cuda()
discriminator = model.Discriminator().cuda()

cp_gen = torch.load(os.path.join(args.checkpoint_dir, 'gen_{}'.format(args.load)))
generator.load_state_dict(cp_gen)
print('Loaded checkpoint (epoch {})'.format(args.load))


labels = [torch.zeros(num_classes).cuda() for i in range(num_classes)]
for i in range(num_classes):
	labels[i][i] = 1

z = torch.randn(64, Z_dim).cuda()


for i in range(num_classes - 1):
	for x in np.arange(0, 1, 0.05):
		label = labels[i + 1] * x + labels[i] * (1.0 - x)
		image = generator(z, label)
		if args.attention:
			discriminator(image, label.unsqueeze(0).expand(64, -1))
			attention = discriminator.attention_output
			upsample = nn.Upsample(scale_factor=4)(attention)
			print('size', upsample.size())
			image = image * upsample[:, 0, :, :].view(64, 1, 32, 32).expand_as(image)

		npimage = image.view(8, 8, 3, 32, 32).permute(2, 0, 3, 1, 4).contiguous().view(3, 8 * 32, 8 * 32)
		npimage = npimage.cpu().detach().numpy()

		scipy.misc.imsave('images/test{0:.2f}.png'.format(i + x), npimage.transpose((1,2,0)))

# make animated gif
with imageio.get_writer('interpolate.gif', mode='I') as writer:
	for filename in sorted(glob('images/*.png'), key=os.path.getmtime):
		writer.append_data(imageio.imread(filename))