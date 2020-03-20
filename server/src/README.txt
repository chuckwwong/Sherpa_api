To use sherpa
 a) Note that a description of the SHERPA system is in the subdirectory sherpa/docs/SHERPA.docxs
 b) make sure your python installation is python 3. The scripts can be run as executables provided their permissions support this, and that your (unix) environment calls up python3 when the command
     % /usr/bin/env python3
 is executed.   Alternatively, you can call the scripts as arguments to the application python3

 c) make sure that your $PYTHONPATH includes the path to the directory in which this README.txt appears,
    'sherpa'

 d) the examples we have from Boeing can be run as follows.  From the command-line in the sherpa directory
       % code/findFlows.py -cmd cmd/flows-script-1

        This will create files session-1.json and flows-1.json in sherpa/exc

       % code/makeEvals.py -cmd cmd/evals-script-1

        You interact with the script to create evaluations and after you are finished the script writes
        those evaluations into the file

         sherpa/exc/evals-1.json


        % code/sherpa.py -cmd cmd/sherpa-script-1

        This creates an output file sherpa/exc/output-1.json


    You can run the topo2 and topo3 examples in exactly the same way, just replacing the string '-1' in the 
    commands above to '-2' or '-3'.

    The results of going through this process for the '-1', '-2', and '-3' sets are recorded 
    in the subdirectory 'examples'


Questions can be passed to the SHERPA developer at dmnicol@illinois.edu



