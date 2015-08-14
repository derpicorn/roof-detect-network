import pdb

import numpy as np
import my_net
import neural_network
from neural_network import Experiment
import utils

from collections import defaultdict


class Ensemble(object):
    def __init__(self, preloaded_paths):
        self.process_preloaded_paths(preloaded_paths)
        self.process_paths_get_nets()

    def predict_proba(self, X, roof_type=None):
        if roof_type is None:
            avg_probs = dict()
            for roof_type, nets in self.neural_nets.iteritems():
                probs = np.array((len(nets),X.shape[0]))
                for n, net in enumerate(nets):
                    probs[n, :]  = net.predict_proba(X)
                avg_probs[roof_type] = np.mean(probs, axis[1])
            return avg_probs
        else:
            probs = np.array((len(self.neural_nets[roof_type]), X.shape[0]))
            for n, net in enumerate(self.neural_nets[roof_type]):
                probs[n, :]  = net.predict_proba(X)
            avg_probs = np.mean(probs, axis=1)
            return avg_probs


    def test(self, X, roof_type, threshold=0.5):
        avg_prob = self.predict_proba(X, roof_type=roof_type)
        return np.array(avg_prob>=threshold, dtype=int)


    def process_preloaded_paths(self, preloaded_paths): 
        #ensure that if we have only one detector, that the network was trained with both types of roof
        #if we have more than one detector, ensure that each was trained on only one type of roof
        self.net_paths = defaultdict(list)
        
        for path in preloaded_paths:
            metal_num = (int(float(utils.get_param_value_from_filename(path, 'metal'))))
            thatch_num = (int(float(utils.get_param_value_from_filename(path,'thatch'))))
            nonroof_num = (int(float(utils.get_param_value_from_filename(path,'nonroof'))))

            assert nonroof_num > 0
            if (metal_num == 0 and thatch_num > 0):
                self.net_paths['thatch'].append(path)
            if (metal_num > 0 and thatch_num == 0):
                self.net_paths['metal'].append(path)


    def process_paths_get_nets(self):
        self.neural_nets = defaultdict(list)
        
        for roof_type, net_paths in self.net_paths.iteritems():
            for p, path in enumerate(net_paths):
                if 'ensemble' in path:
                    start = len('ensemble')+path.find('ensemble')
                    end = path[start:].find('_')
                    starting_batch = int(float(path[start:end]))
                else:
                    starting_batch = 0
                print 'Starting batch is:{}'.format(starting_batch)
                pdb.set_trace()
                neural_params = dict() #one set of parameters per roof type
                neural_param_num = (utils.get_param_value_from_filename(path, 'params'))

                #small hack to pick up right param file number in two cases where I foolishly didn't print it out in the name....
                if neural_param_num is None:
                    if len(net_paths) == 1:
                        neural_param_num = 20005 if roof_type=='thatch' else 20006
                    elif len(net_paths) > 1:
                        neural_param_num = 20003 if roof_type=='thatch' else 20004

                neural_params_fname = 'params{0}.csv'.format(int(neural_param_num)) 

                params_path = '{0}{1}'.format(utils.get_path(params=True, neural=True), neural_params_fname)
                neural_params = neural_network.get_neural_training_params_from_file(params_path)
                neural_params['preloaded_path'] = path
                neural_params['net_name'] = path[:-len('.pickle')] 
                neural_params['roof_type'] = roof_type
                #for each net in the ensemble, we start at a different data batch, that way we get a variety of data for training
                current_net = Experiment(pipeline=True, starting_batch=starting_batch, **neural_params) 
                self.neural_nets[roof_type].append(current_net) 


