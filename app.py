"""
Demonstration:  Ant Colony Optimization for Estimating Pith Position on Images of Tree Log Ends
demo editor: Phuc Ngo
"""

from lib import base_app, build, http, image, config
from lib.misc import app_expose, ctime
from lib.base_app import init_app

import cherrypy
from cherrypy import TimeoutError
import os.path
import shutil
import time

class app(base_app):
    """ template demo app """

    title = "Ant Colony Optimization for Estimating Pith Position on Images of Tree Log Ends: Online Demonstration"
    xlink_article = 'https://www.ipol.im/'
    xlink_src = 'https://www.ipol.im/pub/pre/67/gjknd_1.1.tgz'
    demo_src_filename  = 'gjknd_1.1.tgz'
    demo_src_dir = 'ACO_PithDetection'


    input_nb = 1 # number of input images
    input_max_pixels = 4500 * 4500 # max size (in pixels) of an input image
    input_max_weight = 1 * 4500 * 4500 # max size (in bytes) of an input file
    input_dtype = '3x8i' # input image expected data type
    input_ext = '.png'   # input image expected extension (ie file format)
    is_test = False       # switch to False for deployment
    commands = []
    list_commands = ""


    def __init__(self):
        """
        app setup
        """
        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

        # select the base_app steps to expose
        # index() is generic
        app_expose(base_app.index)
        app_expose(base_app.input_select)
        app_expose(base_app.input_upload)
        # params() is modified from the template
        app_expose(base_app.params)
        # run() and result() must be defined here

    def build(self):
        """
        program build/update
        """
        return


    @cherrypy.expose
    @init_app
    def wait(self, **kwargs):
        """
        params handling and run redirection
        """

        # save and validate the parameters
        try:
            self.cfg['param']['scale'] = kwargs['scale']
            self.cfg['param']['dx'] = kwargs['dx']
            self.cfg['param']['dy'] = kwargs['dy']
            self.cfg['param']['gsigma'] = kwargs['gsigma']
            self.cfg['param']['bsigma'] = kwargs['bsigma']
            self.cfg['param']['lsigma'] = kwargs['lsigma']
            self.cfg['param']['ant'] = kwargs['ant']
            self.cfg['param']['block'] = kwargs['block']
            self.cfg['param']['omega'] = kwargs['omega']
            self.cfg['param']['quantizer'] = kwargs['quantizer']
            self.cfg['param']['alpha'] = kwargs['alpha']
            self.cfg['param']['beta'] = kwargs['beta']
            self.cfg['param']['gamma'] = kwargs['gamma']
            self.cfg['param']['lambda'] = kwargs['lambda']
            self.cfg['param']['iter'] = kwargs['iter']
            self.cfg.save()
        except ValueError:
            return self.error(errcode='badparams',
                              errmsg="The parameters must be numeric.")

        http.refresh(self.base_url + 'run?key=%s' % self.key)
        return self.tmpl_out("wait.html")
    @cherrypy.expose
    @init_app
    def run(self):
        """
        algo execution
        """
        self.list_commands = ""


        try:
            self.run_algo(self)
        except TimeoutError:
            return self.error(errcode='timeout')
        except RuntimeError:
            return self.error(errcode='runtime',
                              errmsg="Something went wrong with the program.")
        except ValueError:
            return self.error(errcode='badparams',
                              errmsg="The parameters given produce no contours,\
                                      please change them.")

        http.redir_303(self.base_url + 'result?key=%s' % self.key)

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.png", "input_0.png", info="Input image")
            ar.add_file("algoLog.txt", info="algoLog.txt")
            ar.add_file("commands.txt", info="commands.txt")
            ar.add_file("Result.png", "Result.png", info="Pith detection result")
            #ar.add_info({"version": self.cfg['param']["version"]})
            ar.save()

        return self.tmpl_out("run.html")


    def run_algo(self, params):
        """
        the core algo runner
        could also be called by a batch processor
        this one needs no parameter
        """

        ## -------
        ## Apply algorithm
        ## ---------
        inputWidth = 512
        inputHeight = 512
        command_args = ['AntColonyPith'] + \
                       ['input_0.png']+ \
                       ['-s', str(self.cfg['param']['scale'])] + \
                       ['-x', str(self.cfg['param']['dx'])]+ \
                       ['-y', str(self.cfg['param']['dy'])]+ \
                       ['-u', str(self.cfg['param']['gsigma'])]+ \
                       ['-v', str(self.cfg['param']['bsigma'])]+ \
                       ['-w', str(self.cfg['param']['lsigma'])]+ \
                       ['-n', str(self.cfg['param']['ant'])]+ \
                       ['-c', str(self.cfg['param']['block'])]+ \
                       ['-o', str(self.cfg['param']['omega'])]+ \
                       ['-q', str(self.cfg['param']['quantizer'])]+ \
                       ['-a', str(self.cfg['param']['alpha'])]+ \
                       ['-b', str(self.cfg['param']['beta'])]+ \
                       ['-g', str(self.cfg['param']['gamma'])]+ \
                       ['-l', str(self.cfg['param']['lambda'])]+ \
                       ['-i', str(self.cfg['param']['iter'])]

        f = open(self.work_dir+"algoLog.txt", "w")
        cmd = self.runCommand(command_args, None, f)
        f.close()
    
        ## ----
        ## Save command line
        ## ----
        f = open(self.work_dir+"commands.txt", "w")
        f.write(self.list_commands)
        f.close()
        return


    @cherrypy.expose
    @init_app
    def result(self, public=None):
        """
        display the algo results
        """
        resultHeight = image(self.work_dir + 'Result.png').size[1]
        imageHeightResized = min (600, resultHeight)
        resultHeight = max(300, resultHeight)
        return self.tmpl_out("result.html", height=resultHeight, \
                             heightImageDisplay=imageHeightResized)


    def runCommand(self, command, stdOut=None, stdErr=None, comp=None):
        """
        Run command and update the attribute list_commands
        """
        p = self.run_proc(command, stderr=stdErr, stdout=stdOut, \
                          env={'LD_LIBRARY_PATH' : self.bin_dir})
        self.wait_proc(p, timeout=500)
        #index = 0
        # transform convert.sh in it classic prog command (equivalent)
        #for arg in command:
        #    if arg == "convert.sh" :
        #        command[index] = "convert"
        #    index = index + 1
        command_to_save = ' '.join(['"' + arg + '"' if ' ' in arg else arg for arg in command ])
        if comp is not None:
            command_to_save += comp
        self.list_commands +=  command_to_save + '\n'
        return command_to_save

  
