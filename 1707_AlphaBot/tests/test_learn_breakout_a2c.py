#!/usr/bin/env python
import os
import time
import logging
import numpy as np

import gym

from baselines import bench
from baselines.common.atari_wrappers import make_atari, wrap_deepmind
from baselines.a2c.policies import CnnPolicy, LstmPolicy, LnLstmPolicy
from baselines import logger
from baselines.common import set_global_seeds, explained_variance
from baselines.common.vec_env.subproc_vec_env import SubprocVecEnv
from baselines.common.atari_wrappers import wrap_deepmind
from baselines.a2c.policies import CnnPolicy
from baselines.a2c.a2c import Model, Runner #learn

import tensorflow as tf


def learn(policy, env, seed, nsteps=5, nstack=4, total_timesteps=int(80e6), vf_coef=0.5, ent_coef=0.01, max_grad_norm=0.5, lr=7e-4, lrschedule='linear', epsilon=1e-5, alpha=0.99, gamma=0.99, log_interval=100):
    tf.reset_default_graph()
    set_global_seeds(seed)

    nenvs = env.num_envs
    ob_space = env.observation_space
    ac_space = env.action_space
    num_procs = len(env.remotes) # HACK
    model = Model(policy=policy, ob_space=ob_space, ac_space=ac_space, nenvs=nenvs, nsteps=nsteps, nstack=nstack, num_procs=num_procs, ent_coef=ent_coef, vf_coef=vf_coef,
        max_grad_norm=max_grad_norm, lr=lr, alpha=alpha, epsilon=epsilon, total_timesteps=total_timesteps, lrschedule=lrschedule)
    runner = Runner(env, model, nsteps=nsteps, nstack=nstack, gamma=gamma)

    nbatch = nenvs*nsteps
    tstart = time.time()
    for update in range(1, total_timesteps//nbatch+1):
        obs, states, rewards, masks, actions, values = runner.run()
        policy_loss, value_loss, policy_entropy = model.train(obs, states, rewards, masks, actions, values)
        nseconds = time.time()-tstart
        fps = int((update*nbatch)/nseconds)
        if update % log_interval == 0 or update == 1:
            ev = explained_variance(values, rewards)
            logger.record_tabular("nupdates", update)
            logger.record_tabular("total_timesteps", update*nbatch)
            logger.record_tabular("fps", fps)
            logger.record_tabular("policy_entropy", float(policy_entropy))
            logger.record_tabular("value_loss", float(value_loss))
            logger.record_tabular("explained_variance", float(ev))
            logger.dump_tabular()
    env.close()

    return model


def test(env_id, num_timesteps, seed, policy, lrschedule, num_cpu):

    DOMODEL = True
    DOTRAIN = False

    nenvs = num_cpu
    nsteps = 5
    nstack = 4

    # Train
    if DOMODEL:

        def make_env(rank):
            def _thunk():
                env = make_atari(env_id)
                env.seed(seed + rank)
                env = bench.Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)))
                gym.logger.setLevel(logging.WARN)
                return wrap_deepmind(env)

            return _thunk

        set_global_seeds(seed)
        env = SubprocVecEnv([make_env(i) for i in range(num_cpu)])
        if policy == 'cnn':
            policy_fn = CnnPolicy
        elif policy == 'lstm':
            policy_fn = LstmPolicy
        elif policy == 'lnlstm':
            policy_fn = LnLstmPolicy

        fsave = 'test_learn_breakout'
        if DOTRAIN:
            # Train
            print('Learning model parameters')
            model = learn(policy_fn, env, seed, nsteps=nsteps, nstack=nstack, total_timesteps=int(num_timesteps * 1.1), lrschedule=lrschedule)
            env.close()
            # Save
            print('Saving model parameters to file')
            model.save(fsave)
        else:
            print('Loading model parameters from file')
            model = learn(policy_fn, env, seed, nsteps=nsteps, nstack=nstack, total_timesteps=10, lrschedule=lrschedule)
            model.load(fsave)

        # Ready for game play?
        input('Press enter to start game: ')

    # Play one game!
    print('Playing!')
    # (init environment)
    env = make_atari(env_id)
    print('log dir:',logger.get_dir())
    env = bench.Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)))
    env = wrap_deepmind(env)
    obs = env.reset()
    # (init observations stack)
    nh, nw, nc = env.observation_space.shape
    allobs = np.zeros((nenvs, nh, nw, nc * nstack), dtype=np.uint8)
    allobs[0][:, :, -nc:] = obs
    # (play)
    for update in range(1, 10001):
        env.render()
        time.sleep(.1)
        if DOMODEL:
            if update == 1:
                states = model.initial_state
                action = env.action_space.sample()
            else:
                actions, values, states = model.step(allobs, states, done)
                action = actions[0]
        else:
            action = env.action_space.sample()
        obs, reward, done, _ = env.step(action)
        if done:
            obs = env.reset()
        allobs = np.roll(allobs, shift=-nc, axis=3)
        allobs[0][:, :, -nc:] = obs
    env.close()




test('BreakoutNoFrameskip-v4', num_timesteps=1e6, seed=0,
      policy='cnn',             # 'cnn', 'lstm', 'lnlstm'
      lrschedule='constant',    # 'constant', 'linear'
      num_cpu=16)

