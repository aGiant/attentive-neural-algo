import tensorflow as tf
import numpy as np
import trfl, gym

from collections import deque
from attentive_np.attentive_np import Attention, LatentModel
from attentive_np.cartpole_reader import *

class QNetwork(object):

	def __init__(self, name, model, learning_rate=0.01, state_size=4,
				 action_size=2, hidden_size=128, batch_size=64, context_size=32):

		with tf.variable_scope(name):
			self._model = model

			self._context_x = tf.placeholder(tf.float32, [batch_size, context_size, state_size])
			self._context_y = tf.placeholder(tf.int32, [batch_size, context_size, action_size])
			self._target_x  = tf.placeholder(tf.float32, [batch_size, 1, state_size])

			self._query = ((self._context_x, self._context_y), self._target_x)

			self._actions = tf.placeholder(tf.int32, [batch_size], name='actions')

			self.output = model(self._query, 1)

			#self.rep = tf.squeeze(tf.concat([self.mu, self.sigma], axis=1))

			#self.output = tf.contrib.layers.fully_connected(self.rep, action_size,
			#	activation_fn=None)

			self.name = name

			self._targetQs = tf.placeholder(tf.float32, [batch_size, action_size], name='target')
			self.reward = tf.placeholder(tf.float32, [batch_size], name='reward')
			self.discount = tf.constant(0.99, shape=[batch_size], dtype=tf.float32, name='discount')

			q_loss, q_learning = trfl.double_qlearning(self.output, self._actions, self.reward,
													   self.discount, self._targetQs, self.output)
			self.loss = tf.reduce_mean(q_loss)
			self.opt = tf.train.AdamOptimizer(learning_rate).minimize(self.loss)

class Memory(object):

	def __init__(self, max_size=1000):

		self.buffer = deque(maxlen=max_size)

	def add(self, experience):
			self.buffer.append(experience)

	def sample(self, batch_size):
			idx = np.random.choice(np.arange(len(self.buffer)),
								   size=batch_size,
								   replace=False)

			return [self.buffer[ii] for ii in idx]

def copy_model_parameters(sess, estimator1, estimator2):

	e1_params = [t for t in tf.trainable_variables() if t.name.startswith(estimator1.name)]
	e1_params = sorted(e1_params, key=lambda v: v.name)
	e2_params = [t for t in tf.trainable_variables() if t.name.startswith(estimator2.name)]
	e2_params = sorted(e2_params, key=lambda v: v.name)

	update_ops = []
	for e1_v, e2_v in zip(e1_params, e2_params):
		op = e2_v.assign(e1_v)
		update_ops.append(op)

	sess.run(update_ops)
