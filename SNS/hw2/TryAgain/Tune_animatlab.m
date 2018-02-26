classdef Tune_animatlab < hgsetget
    %TUNE_ANIMATLAB Class that allows a user to tune simulations in
    %AnimatLab. It allows the user to simply specify the parameters to
    %manipulate and an objective function to minimize (least squares with
    %joint kinematics, response spectrum of a control system, output of a
    %neural system, etc.), and this program handles all of the details.
    %neuromechanical simulations
    %   HOW TO USE TUNE_ANIMATLAB
    %       SETTING UP YOUR ANIMATLAB SIMULATION
    %       To use this class, the user must first build a simulation in
    %       AnimatLab that they wish to tune. Objects should have unique
    %       and distinctive names to facilitate changing parameters. A
    %       system of ten neurons all named "1" will not yield successful
    %       results with this program. In addition, each item that you wish
    %       to be varied independently should be named separately. For
    %       example, changing the conductivity of a synapse will change the
    %       conductivity of all synapses with that name. So do not use the
    %       same synapse type for more than one connection unless you
    %       really want them to be identical.
    %
    %       TUNE_ANIMATLAB will import data exported via a line chart to
    %       produce the behavior you want. Therefore you should make a line
    %       chart with the outputs your objective function will need to
    %       measure performance. You should run your simulation in
    %       AnimatLab and export the data chart to make sure you know which
    %       column holds what data. When TUNE_ANIMATLAB runs your file,
    %       every column will be shifted one to the right after the
    %       addition of a "timeslice" column on the left, so plan
    %       accordingly.
    %
    %       Your simulation settings will need to be correct to make proper
    %       use of this TUNE_ANIMATLAB. In the SIMULATION (root) branch of
    %       the tree in AnimatLab, set the "Set Sim To End" flag to "True."
    %       Set "Sim End Time" to any number larger than the end time of
    %       your data line chart. If you wish to collect more or less data,
    %       change these both accordingly. My rule of thumb is to make "Set
    %       Sim To End" 0.02 seconds longer than the data chart end time. I
    %       also recommend that "Playback Control Mode" is set to
    %       "FastestPossible."
    %
    %       One branch below SIMULATION is ENVIRONMENT. The physics engine
    %       adds noise to make subsequent simulations different from one
    %       another. In order for the optimization to work as quickly as
    %       possible, "AutoGenerate Random Seed" should be set to false.
    %       This means it will use the same random numbers in each trial,
    %       meaning that the simulations will have random noise, but each
    %       trial will have the SAME random noise, allowing subsequent
    %       simulations to be identical. Otherwise the optimization
    %       routines will never converge. You can set "Manual Random Seed"
    %       to whatever value you wish.
    %
    %       Your AnimatLab file is now ready to export. Ensuring that your
    %       data line chart is currently open, click File>Export Standalone
    %       Simulation. A dialog will pop up. Keep all of the default
    %       values EXCEPT "Show graphics window." If you want to watch your
    %       simulation every iteration, leave this box checked. However,
    %       the program will run much faster if this is unchecked.
    %
    %       SETTING UP TUNE_ANIMATLAB
    %       To most easily use this class, first create a script in which
    %       you declare your variables and construct the object. The
    %       constructor takes up to eight inputs. 
    %
    %       sim_file - String of the full path of the .asim file that you
    %       exported from AnimatLab.
    %
    %       input_variables_cell - An nx3 cell array of the variables that
    %       you wish to optimize. Each row holds a property. The columns
    %       are the object type, the object name, and the property name.
    %       The private variable animatlab_properties holds the options for
    %       use. The object types are commented out above each column of
    %       animatlab_properties. The object name is as read in AnimatLab.
    %       The user may also specify 'all' to modify all objects of a type
    %       (all neurons, all muscles, etc.). The properties are the first
    %       column of animatlab_properties. Again, the user may specify
    %       'all' to change all of an object's properties.
    %
    %       desired_output_data_file - A string that is the name of the
    %       .mat file that holds desired
    %       kinematic data for optimization. The first column should be
    %       time (in seconds), and the subsequent columns should be system
    %       states at those timesteps. In the user's objective function,
    %       these columns should be mapped to simulation output; this is
    %       not handled by this class, as it never directly makes any
    %       comparisons between desired and actual system output.
    %
    %       sim_output_data_file - A string that is the name of the line 
    %       chart in AnimatLab that will be read for simualation 
    %       evaluation.
    %
    %       objective_function - A string that is the name of the function
    %       that will analyze simulation output. It must take two inputs:
    %       a cell array in which each element holds the output from one
    %       simulation; and a matrix of the desired data, as read from
    %       desired_output_data_file. Other parameters such as penalties
    %       may be hard-coded into the function. This function may call
    %       other functions. This function must be saved on the path.
    %
    %       sims_folder - A string that is the directory of a folder in
    %       which Tune_animatlab will save simulation files to execute by
    %       AnimatLab. This folder should be on a hard drive with plenty of
    %       free space (5GB or more).
    %
    %       performance_folder - 
    %
    %       source_folder - A string that is the directory of the \bin
    %       folder inside the AnimatLab installation directory. Must
    %       include \bin itself.
    
    properties
        sim_file_text; %Cell array that holds a line-by-line copy of the .asim file
        sim_file_length; %Number of rows in the sim file
        sim_file = 'F:\Documents\Animatlab\Cockroach20150220b-LM only_No mesh\Cockroach20150220b-LM only_No mesh_Standalone.asim';
        sim_output_data_file = 'LM Control';
        sims_folder = 'F:\My Documents\SimFiles';
        performance_folder = 'F:\My Documents\Performance Data\Training with Animatlab\Mantis';
        source_folder = 'F:\Program Files and Installations\AnimatLab\bin';
        user_objective_function = 'nlls';
        initial_values; %values of the variables from the simulation
        optimization_variables = cell(0,6); %System-formatted cell array of the type, name, property, bounds, and scale of each object to optimize. 
    end
    
    properties (Access = private)
        aproj_file = []; %Directory of the .aproj file, which runs in AnimatLab.
        input_variables = {}; %User-formatted cell array of the type, name, and property of each object to optimize.
        desired_output; %The first column is time. User should check the order of the columns for their objective function
        desired_output_file = []; %Name of the file that holds the desired system output. The first column is time in seconds.
        variable_name_indices; %Index of the object (neuron, synapse, etc.) in sim_file_text;
        variable_indices; %1 row for each variable: index of the value in sim_file_text, the first index of the numerical value, and the final index of the numerical value
        final_values = []; %values of the variables after optimization
        bounds; %limits on variable values. first column = low, second column = high
        animatlab_bounds; %limits that AnimatLab places on variable values. These can never be violated.
        output_data_size = []; %size of the data matrix we get from running one simulation.
        time_vec = []; %time vector for the output data
        scan_parameter_data = {}; %data from the most recent "parameter scan," generated by obj.scan_parameter()
        plot_time_limits;
        plot_time_indices;
        inds_within_bounds = []; %list of parameter sets that are entirely within the bounds of the optimization routine.
        inds_outside_bounds = []; %list of parameter sets in which any variable is outside the bounds of the optimization routine.
        need_to_set_plot_time_limits = false; %boolean of whether we need to call set_plot_time_limits to find the first and last indices of data for the user.
        to_parallelize = false; %boolean of whether to parallelize simulation runs or not
        pp = []; %parpool object for parallelizing simulations
        num_threads = 1; %number of workers available on this machine
        col_headers = [];
        
        %These are formatted to match AnimatLab, and should never be
        %changed either by this program or the user.
        animatlab_properties = {%neuron
                                {   'TonicStimulus',-1e-06,1e-06,'TonicStimulus',1e-9;...
                                    'RestingPot',-100e-3,100e-3,'RestingPotential',1e-3;...
                                    'Size',1e-06,100,'RelativeSize',1;...
                                    'TimeConst',1e-5,10,'TimeConstant',1e-3;...
                                    'GMaxCa',0,100e-6,'MaxCaConductance Value',1e-6;...
                                    'mMidPoint',-0.2,0.2,'Midpoint Value',1e-3;...
                                    'mSlope',0.010,10,'Slope Value',1;...
                                    'mTimeConstant',0.001,100,'TimeConstant Value',1e-3;...
                                    'hMidPoint',-0.2,0.2,'Midpoint Value',1e-3;...
                                    'hSlope',-10,-.010,'Slope Value',1;...
                                    'hTimeConstant',0.001,100,'TimeConstant Value',1e-3;...
                                    'InitialThresh',-100e-3,100e-3,'InitialThreshold Value',1e-3;...
                                    'RelativeAccom',0,1,'RelativeAccomodation Value',1;...
                                    'AccomTimeConst',1e-3,1,'AccomodationTimeConstant Value',1e-3;...
                                    'AHPAmp',0,100e-6,'AHP_Conductance Value',1e-6;...
                                    'AHPTimeConst',1e-3,100e-3,'AHP_TimeConstant Value',1e-3};...
                                %nonspikingsynapse    
                                {   'Equil',-0.1,0.3,'EquilibriumPotential Value',1e-3;...
                                    'SynAmp',0,100e-6,'MaxSynapticConductance Value',1e-6;...
                                    'ThreshV',-0.1,0.3,'PreSynapticThreshold Value',1e-3;...
                                    'SaturateV',-0.1,0.3,'PreSynapticSaturationLevel Value',1e-3};...
                                %spikingsynapse
                                {   'Equil',-100e-3,300e-3,'EquilibriumPotential Value',1e-3;...
                                    'SynAmp',0,100e-6,'SynapticConductance Value',1e-6;...
                                    'Decay',0.01e-3,1000e-3,'DecayRate Value',1e-3;...
                                    'RelFacil',0,10,'RelativeFacilitation Value',1;...
                                    'FacilDecay',0.01e-3,1000e-3,'FacilitationDecay Value',1e-3;...
                                    'MaxRelCond',1,1000,'MaxRelativeConductance Value',1;...
                                    'SatPSPot',-100e-3,100e-3,'SaturatePotential Value',1e-3;...
                                    'ThreshPSPot',-100e-3,100e-3,'ThresholdPotential Value',1e-3};...
                                %electricalsynapse
                                {   'TurnOnV',-100e-3,300e-3,'TurnOnThreshold Value',1e-3;...
                                    'SaturateV',-100e-3,300e-3,'TurnOnSaturate Value',1e-3;...
                                    'LowCoup',0,100e-6,'LowCoupling Value',1e-6;...
                                    'HiCoup',0,100e-6,'HighCoupling Value',1e-6};...
                                %adapter    
                                {   'A',-1e6,1e6,'A Value',1;...
                                    'B',-1e6,1e6,'B Value',1;...
                                    'C',-1e6,1e6,'C Value',1;...
                                    'D',-1e6,1e6,'D Value',1;...
                                    'LowerLimit',-1e18,1e18,'LowerLimitScale',1;...
                                    'UpperLimit',-1e18,1e18,'UpperLimitScale',1;...
                                    'LowerOutput',-1e18,1e18,'LowerOutputScale',1;...
                                    'UpperOutput',-1e18,1e18,'UpperOutputScale',1};...
                                %muscle
                                {   'A',-100e-3,300e-3,'A Value',1;... %x-offset
                                    'B',0,100,'B Value',1;... %amplitude
                                    'C',0,1000,'C Value',1;... %steepness
                                    'D',-10,10,'D Value',1;... %y-offset
                                    'RestingLength',0,1e3,'RestingLength Value',1;...
                                    'Lwidth',0,1e3,'Lwidth Value',1;...
                                    'Kse',0,1e6,'Kse Value',1;...
                                    'Kpe',0,1e6,'Kpe Value',1;...
                                    'damping',0,1e6,'B value',1};...
                                %stimulus    
                                {   'StartTime',0,1000,'StartTime Value',1;...
                                    'EndTime',0,1000,'EndTime Value',1;...
                                    'CurrentOn',-1e-07,1e-07,'CurrentOn Value',1;...
                                    'Equation',-1e9,1e9,'Equation',1;...
                                    'CurrentOnEquation',-1e9,1e9,'Equation',1}
                                };
        
        ca_props = {'GMaxCa';'MidPoint';'Slope';'TimeConstant';'ActivationType'};
    end
    
    methods
        function obj = Tune_animatlab(sim_file,input_variables_cell,desired_output_data_file,sim_output_data_file,objective_function,sims_folder,performance_folder,source_folder)
            
            if nargin == 0
                
            elseif nargin == 1
                obj.sim_file = sim_file;
            elseif nargin == 2
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
            elseif nargin == 3
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
            elseif nargin == 4
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
                obj.sim_output_data_file = sim_output_data_file;
            elseif nargin == 5
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
                obj.sim_output_data_file = sim_output_data_file;
                obj.user_objective_function = objective_function;
            elseif nargin == 6;
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
                obj.sim_output_data_file = sim_output_data_file;
                obj.user_objective_function = objective_function;
                obj.sims_folder = sims_folder;
            elseif nargin == 7;
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
                obj.sim_output_data_file = sim_output_data_file;
                obj.user_objective_function = objective_function;
                obj.sims_folder = sims_folder;
                obj.performance_folder = performance_folder;
            else
                obj.sim_file = sim_file;
                obj.input_variables = input_variables_cell;
                obj.desired_output_file = desired_output_data_file;
                obj.sim_output_data_file = sim_output_data_file;
                obj.user_objective_function = objective_function;
                obj.sims_folder = sims_folder;
                obj.performance_folder = performance_folder;
                obj.source_folder = source_folder;
            end
            
            %Read and save the desired output to object properties
            if isempty(obj.desired_output_file)
                warning('No desired output file specified.');
                obj.desired_output = [];
            elseif length(obj.desired_output_file) > 4 && strcmp(obj.desired_output_file(end-3:end),'.txt')
                obj.desired_output = obj.read_text_file(obj.desired_output_file);
            elseif length(obj.desired_output_file) > 4 && strcmp(obj.desired_output_file(end-3:end),'.mat')
                %If we load a .mat file, then we can write it to a struct,
                %and we must then go through the struct to find the actual
                %data. Presumably there is only one entry. But just in
                %case, we cycle through and accept the first entry that is
                %of type "double."
                data_struct = load(obj.desired_output_file);
                field_names = fieldnames(data_struct);
                continue_to_loop = true;
                i = 1;
                while continue_to_loop
                    temp_data = getfield(data_struct,field_names{i});
                    if isa(temp_data,'double')
                        obj.desired_output = temp_data;
                        continue_to_loop = false;
                    end
                    i = i + 1;
                    if i > length(field_names)
                        continue_to_loop = false;
                    end
                    clear temp_data
                end
            elseif isempty(obj.desired_output_file)
                obj.desired_output = [];
            else
                error('Desired output file type not recognized.')
            end
            
            %Set up parallelization based on the type of obj.sims_folder
            
            if ischar(obj.sims_folder)
                obj.to_parallelize = false;
            elseif iscell(obj.sims_folder)
                delete(gcp)
                obj.to_parallelize = true;
                try obj.pp = parpool(length(obj.sims_folder));
                catch
                    warning(['This machine cannot provide the requested ',...
                        num2str(length(obj.sims_folder)),' workers. A smaller pool will be started instead.'])
                    obj.pp = parpool;
                end
                obj.num_threads = obj.pp.NumWorkers;
            end
            
            %Assume that the simulation file matches the folder name, and
            %save it.
%             slash_indices = strfind(obj.sim_file,'\')
%             project_folder = obj.sim_file(1:slash_indices(end))
%             if length(slash_indices) > 1
%                 obj.aproj_file = [project_folder,project_folder(slash_indices(end-1)+1:slash_indices(end)-1),'.aproj']
%             else
%                 obj.aproj_file = [project_folder,project_folder(slash_indices+1:slash_indices(end)-1),'.aproj']
%             end
            
            dot_index = strfind(obj.sim_file,'.');
            filename = obj.sim_file(1:dot_index(1));
            obj.aproj_file = [filename,'aproj'];
                
            obj.check_variables_and_initial_values();
            obj.clean_sims_folder();
        end
        
        function ICs = check_variables_and_initial_values(obj)

            try obj.sim_file_text = obj.read_text_file(obj.sim_file);
            catch
                error([obj.sim_file,' does not exist.'])
            end
                
            obj.sim_file_length = length(obj.sim_file_text);
            %Now we will fill obj.optimization_variables Each row will hold one property from
            %the simulation file to change during the simulation.
            obj.variable_name_indices = [];
            obj.optimization_variables = {};

            for i=1:size(obj.input_variables,1)
                temp_props = cell(0,5);
                if strcmp(obj.input_variables{i,2},'all')
                    %If we want all of an object type
                    if strcmp(obj.input_variables{i,1},'neuron')
                        %Neurons
                        %Find where the segment of the file that stores Neuron
                        %information begins and ends
                        lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<Neurons>')),1,'first');
                        upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</Neurons>')),1,'first');

                        %Find the indices of the names of all the neurons
                        neur_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));
                        %obj.variable_name_indices(end+1:end+length(neur_name_ind),1) = neur_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(neur_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{neur_name_ind(j)}(7:end-7); %#ok<AGROW>
                        end
                        
                        %Enter the type as neuron
                        temp_props(end+1-length(neur_name_ind):end,1) = {'neuron'};

                    elseif length(obj.input_variables{i,1}) >= 8 && strcmp(obj.input_variables{i,1}(end-6:end),'synapse')
                        %Synapses
                        %Find where the segment of the file that stores Synapse
                        %information begins and ends
                        if strcmp(obj.input_variables{i,1}(1),'s')
                            lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<SpikingSynapses>')),1,'first');
                            upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</SpikingSynapses>')),1,'first');
                        elseif strcmp(obj.input_variables{i,1}(1),'n')
                            lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<NonSpikingSynapses>')),1,'first');
                            upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</NonSpikingSynapses>')),1,'first');
                        elseif strcmp(obj.input_variables{i,1}(1),'e')
                            lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<ElectricalSynapses>')),1,'first');
                            upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</ElectricalSynapses>')),1,'first');
                        end
                        %Find the indices of the names of all the synapses of the
                        %specified type
                        syn_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));
                        %obj.variable_name_indices(end+1:end+length(syn_name_ind),1) = syn_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(syn_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{syn_name_ind(j)}(7:end-7);%#ok<AGROW>
                        end
                        
                        %Enter the type as synapse
                        temp_props(end+1-length(syn_name_ind):end,1) = {'synapse'};

                    elseif strcmp(obj.input_variables{i,1},'inputadapter')
                        %Adapters
                        %Find where the segment of the file that stores Adapter
                        %information begins and ends
                        lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<Adapters>')),1,'first');
                        upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</Adapters>')),1,'first');

                        %Find the indices of the names of all the adapters
                        adapter_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));

                        %Find the indices of the input adapters
                        adapter_type_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Type>PhysicalToNode</Type>')));

                        %Also find the type of adapter, input or output, 
                        adapter_name_ind = intersect(adapter_name_ind,adapter_type_ind-2);
                        %obj.variable_name_indices(end+1:end+length(adapter_name_ind),1) = adapter_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(adapter_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{adapter_name_ind(j)}(7:end-7);%#ok<AGROW>
                        end
                        
                        %Enter the type as adapter
                        temp_props(end+1-length(adapter_name_ind):end,1) = {'adapter'};

                    elseif strcmp(obj.input_variables{i,1},'outputadapter')
                        %Adapters
                        %Find where the segment of the file that stores Adapter
                        %information begins and ends
                        lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<Adapters>')),1,'first');
                        upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</Adapters>')),1,'first');

                        %Find the indices of the names of all the adapters
                        adapter_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));

                        %Find the indices of the input adapters
                        adapter_type_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Type>NodeToPhysical</Type>')));

                        %Also find the type of adapter, input or output, 
                        adapter_name_ind = intersect(adapter_name_ind,adapter_type_ind-2);
                        %obj.variable_name_indices(end+1:end+length(adapter_name_ind),1) = adapter_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(adapter_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{adapter_name_ind(j)}(7:end-7);%#ok<AGROW>
                        end
                        
                        %Enter the type as adapter
                        temp_props(end+1-length(adapter_name_ind):end,1) = {'adapter'};

                    elseif strcmp(obj.input_variables{i,1},'muscle')             
                        %<Type>LinearHillMuscle
                        %Muscles
                        %Find where the segment of the file that stores muscle
                        %information begins and ends
                        lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<ChildBodies>')),1,'first');
                        upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</ChildBodies>')),1,'last');

                        %Find the indices of the names of all the muscles
                        muscle_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));

                        %Find the indices of the type of muscle
                        muscle_type_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Type>LinearHillMuscle</Type>')));

                        %Also find the type of adapter, input or output, 
                        muscle_name_ind = intersect(muscle_name_ind,muscle_type_ind-2);
                        %obj.variable_name_indices(end+1:end+length(muscle_name_ind),1) = muscle_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(muscle_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{muscle_name_ind(j)}(7:end-7);%#ok<AGROW>
                        end
                        
                        %Enter the type as adapter
                        temp_props(end+1-length(muscle_name_ind):end,1) = {'muscle'};
                    elseif strcmp(obj.input_variables{i,1},'stimulus')             
                        %Find where the segment of the file that stores muscle
                        %information begins and ends
                        lower_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'<ExternalStimuli>')),1,'first');
                        upper_limit = find(~cellfun(@isempty,strfind(obj.sim_file_text,'</ExternalStimuli>')),1,'last');

                        %Find the indices of the names of all the adapters
                        stim_name_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Name>')));

                        %Find the indices of the input adapters
                        stim_type_ind = lower_limit - 1 + find(~cellfun(@isempty,strfind(obj.sim_file_text(lower_limit:upper_limit),'<Type>Stimulus</Type>')));

                        %Also find the type of adapter, input or output, 
                        stim_name_ind = intersect(stim_name_ind,stim_type_ind-2);
                        %obj.variable_name_indices(end+1:end+length(stim_name_ind),1) = stim_name_ind;
                        
                        %Save the name of the properties we are going to change
                        for j=1:length(stim_name_ind)
                            temp_props{end+1,2} = obj.sim_file_text{stim_name_ind(j)}(7:end-7);%#ok<AGROW>
                        end
                        
                        %Enter the type as adapter
                        temp_props(end+1-length(stim_name_ind):end,1) = {'stimulus'};

                    else
                        if strcmp(obj.input_variables{i,1},'synapse')
                            error('Synapses need qualifying letters (s, n, e) in front.')
                        end
                        return
                    end
                else
                    if strcmp(obj.input_variables{i,1},'neuron')
                        %Neurons

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>

                        %Enter the type as neuron
                        temp_props(end,1) = {'neuron'};

                    elseif length(obj.input_variables{i,1}) >= 16 && strcmp(obj.input_variables{i,1}(end-16:end),'nonspikingsynapse')
                        %Synapses

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>
                        
                        %Enter the type as synapse
                        temp_props(end,1) = {'nonspikingsynapse'};
                        
                    elseif length(obj.input_variables{i,1}) >= 13 && strcmp(obj.input_variables{i,1}(end-13:end),'spikingsynapse')
                        %Synapses

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>
                        
                        %Enter the type as synapse
                        temp_props(end,1) = {'spikingsynapse'};
                        
                    elseif length(obj.input_variables{i,1}) >= 16 && strcmp(obj.input_variables{i,1}(end-16:end),'electricalsynapse')
                        %Synapses

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>
                        
                        %Enter the type as synapse
                        temp_props(end,1) = {'electricalsynapse'};
                        
                    elseif strcmp(obj.input_variables{i,1},'inputadapter')...
                            || strcmp(obj.input_variables{i,1},'outputadapter')...
                            || strcmp(obj.input_variables{i,1},'adapter')
                        %Adapters

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>

                        %Enter the type as adapter
                        temp_props(end,1) = {'adapter'};

                    elseif strcmp(obj.input_variables{i,1},'muscle')             
                        %Muscles

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>

                        %Enter the type as adapter
                        temp_props(end,1) = {'muscle'};
                    elseif strcmp(obj.input_variables{i,1},'stimulus')
                        %Stimuli

                        %Save the name of the properties we are going to change
                        temp_props(end+1,2) = obj.input_variables(i,2);%#ok<AGROW>

                        %Enter the type as stimulus
                        temp_props(end,1) = {'stimulus'};
                    else
                        error(['Object type "',obj.input_variables{i,1},'" is not recognized.'])
                    end
                end

                %Each combination of neurons, synapses, muscles, and adapters needs
                %a list of changeable properties. The properties are kept in
                %separate lists within the cell, indexed this way.
                if strcmp(temp_props(1,1),'neuron')
                    list = 1;
                elseif strcmp(temp_props(1,1),'nonspikingsynapse')
                    list = 2;
                elseif strcmp(temp_props(1,1),'spikingsynapse')
                    list = 3;
                elseif strcmp(temp_props(1,1),'electricalsynapse')
                    list = 4;
                elseif strcmp(temp_props(1,1),'adapter')
                    list = 5;
                elseif strcmp(temp_props(1,1),'muscle')
                    list = 6;
                elseif strcmp(temp_props(1,1),'stimulus')
                    list = 7;
                end
                
                %If we want all the properties for a given object, 
                if strcmp(obj.input_variables{i,3},'all')
                    %Find how many properties we can change for this object
                    num_props = size(obj.animatlab_properties{list},1);

                    %Find out how many properties "slots" we are trying to fill (to
                    %export to our optimizer)
                    num_objects = size(temp_props,1);

                    %Make a temporary cell array to hold all these properties
                    new_temp_props = cell(size(obj.animatlab_properties{list},1)*size(temp_props,1),6);
                    %Store the actual names of the object types, objects, and
                    %properties in the cell array new_temp_props. Also include the
                    %limits (columns 4 and 5).
                    for j=1:num_objects
                        new_temp_props((j-1)*num_props+1:j*num_props,1) = temp_props(j,1);
                        new_temp_props((j-1)*num_props+1:j*num_props,2) = temp_props(j,2);
                        % %
                        new_temp_props((j-1)*num_props+1:j*num_props,3:6) = obj.animatlab_properties{list}(:,[1:3,5]);
                    end
                    %Save the results.
                    temp_props = new_temp_props;
                else
                    %If we don't have a big block of them to save, then we need to
                    %do what the code above does on an entry-by-entry basis.
                    prop_to_use = find(~cellfun(@isempty,strfind(obj.animatlab_properties{list}(:,1), obj.input_variables{i,3})),1,'first');
                    if any(~cellfun(@isempty,strfind(obj.animatlab_properties{list}(:,1), obj.input_variables{i,3})))
                        temp_props(:,3:6) = repmat(obj.animatlab_properties{list}(prop_to_use,[1:3,5]),size(temp_props,1),1);
                    else
                        error(['Requested property ',obj.input_variables{i,3},' is not an option.']);             
                    end
                end
                obj.optimization_variables(end+1:end+size(temp_props,1),:) = temp_props;
            end
            
            %Now, find these values in the text, and read out their current
            %values
            ICs = zeros(size(obj.optimization_variables,1),1);
            obj.variable_name_indices = zeros(size(ICs));
            
            for i=1:size(obj.optimization_variables,1)
                %Put the desired name into the format seen in the .asim file, that
                %is, label it as "name" or "ID". Neurons, rigid bodies, synapse
                %types, and adapters all use the Name identifier. Individual
                %synapses use the ID identifier.
                if strcmp(obj.optimization_variables{i,2}(1),'<')
                    name_to_find = obj.optimization_variables{i,2};
                else
                    name_to_find = ['<Name>',obj.optimization_variables{i,2},'</Name>'];
                end
                
                name_index_bool = strfind(obj.sim_file_text,name_to_find);
                
                lower_limit = find(~cellfun(@isempty,name_index_bool),1,'first');
                try obj.variable_name_indices(i) = lower_limit;
                catch
                    error(['Variable "',name_to_find(7:end-7),'" not found in the standalone simulation file.'])
                end
                
                %If the prop_to_find is a calcium current related value, we need to
                %pick a different lower limit based on whether the property is for
                %calcium activation or deactivation. The .asim files handle these
                %properties differently, so they need special treatment.
                if any(strcmp(obj.optimization_variables{i,3}(2:end),obj.ca_props))
                    if strcmp(obj.optimization_variables{i,3}(1),'m')
                        %Activation
                        name_to_find = '<CaActivation>';
                    elseif strcmp(obj.optimization_variables{i,3}(1),'h')
                        %Deactivation
                        name_to_find = '<CaDeactivation>';
                    end
                    %Find the proper "activation" or "deactivation" string and
                    %adjust the lower limit. Then
                    %name_index_bool = strfind(original_text(lower_limit:end),name_to_find);
                    name_index_bool = strfind(obj.sim_file_text(lower_limit:end),name_to_find);
                    lower_limit = lower_limit + find(~cellfun(@isempty,name_index_bool),1,'first');
                    %remove the m or h so we can find it in the file.
                    prop_to_find = ['<',obj.optimization_variables{i,3}(2:end),'>'];
                    which_to_find = 1;
                elseif strcmp(obj.optimization_variables{i,3},'damping')
                    %We should find muscle damping, which is actually called "B,"
                    %just like the muscle activation's curve. Therefore we need to
                    %be a little more specific. We want the second B that shows up
                    %for a particular muscle.
                    prop_to_find = '<B>';
                    which_to_find = 2;
                else
                    %Now find the desired property, formatted like the file.
                    prop_to_find = ['<',obj.optimization_variables{i,3},'>'];
                    which_to_find = 1;
                end
                
                %Find that string in the file, the first time after the lower limit
                %(where the named object is found). 
                property_index_bool = strfind(obj.sim_file_text(lower_limit:end),prop_to_find);
                
                 %Find the index at which this occurs, and save this for quick
                %reference later. Remember that we were only examining
                %original_text after the lower_limit, so we need to add that back
                %on. -1 makes the indexing work properly.

                try
                    all_property_indices = find(~cellfun(@isempty,property_index_bool)) + lower_limit - 1;
                catch
                    error(['The item "',obj.optimization_variables{i,2},'" or its property "',prop_to_find,'" does not exist.'])
                end
                
                if isempty(all_property_indices)
                    error(['The item "',obj.optimization_variables{i,2},'" or its property "',prop_to_find,'" does not exist.'])
                end                    
                
                obj.variable_indices(i,1) = all_property_indices(which_to_find);
                
                %Find the final index of the row to keep before the number begins
                obj.variable_indices(i,2) = length(prop_to_find) + 1;
                %Find the first index of the row to keep after the number begins
                obj.variable_indices(i,3) = cell2mat(strfind(obj.sim_file_text(obj.variable_indices(i,1)),'</')) - 1;
                
                ICs(i) = str2double(obj.sim_file_text{obj.variable_indices(i,1)}(obj.variable_indices(i,2):obj.variable_indices(i,3)));
                obj.initial_values = ICs;
                %these can never be violated; save them and don't change
                %them
                obj.animatlab_bounds = cell2mat(obj.optimization_variables(:,4:5))./repmat(cell2mat(obj.optimization_variables(:,6)),1,2);
                
                %These are the bounds used for optimization. By default,
                %they are the animatlab_bounds, but they can be changed by
                %the user to anything MORE restrictive.
                obj.bounds = obj.animatlab_bounds;
            end
            
            %Make sure the file doesn't start paused.
            if strcmp(obj.sim_file_text{5},'<StartPaused>True</StartPaused>')
                obj.sim_file_text{5} = '<StartPaused>False</StartPaused>';
            end            
        end
        
        function [simulation_data,column_headers] = vary_params_run_sims(obj,new_variable_values)
            if size(new_variable_values,1) ~= length(obj.initial_values)
                error('Method vary_params was passed an invalid set of values.')
            end
            
            [num_variables,num_variations] = size(new_variable_values);
            places = ceil(log10(num_variations));
            
            num_variations_vec = zeros(obj.num_threads,1);
            for i=1:num_variations
                j = mod(i-1,obj.num_threads)+1;
                num_variations_vec(j) = num_variations_vec(j) + 1;
            end
            
            files_to_run = cell(obj.num_threads,max(num_variations_vec));
                        
            for i=1:obj.num_threads
                for j=1:num_variations_vec(i)

                    variable_index = sum(num_variations_vec(1:i-1)) + j;
                    if any(new_variable_values(:,variable_index) < obj.bounds(:,1)) ||...
                            any(new_variable_values(:,variable_index) > obj.bounds(:,2))
                        warning(['Attempted variable values from trial ',num2str(variable_index),' are outside the bounds.'])
                    end
                    
                    new_sim_file_text = obj.sim_file_text; 
                    %We will modify the original text to make a new trial
                    for k=1:num_variables
                        %For each variable, copy the original line from the sim
                        %file and replace the numerical value.            
                        current_text = obj.sim_file_text{obj.variable_indices(k,1)};
                        new_text = [current_text(1:obj.variable_indices(k,2)-1),num2str(new_variable_values(k,variable_index)),current_text(obj.variable_indices(k,3)+1:end)];
                        new_sim_file_text{obj.variable_indices(k,1)} = new_text;
                    end
                    %Generate the file name. Save it in the sims folder with the simple
                    %name sim_(number).asim. Note that (number) is padded with 0s
                    %to maintain the order.
                    if obj.to_parallelize
                        save_file_str = [obj.sims_folder{i},'\sim_',repmat('0',1,places-ceil(log10(j+1))),num2str(j),'.asim'];      
                    else
                        save_file_str = [obj.sims_folder,'\sim_',repmat('0',1,places-ceil(log10(j+1))),num2str(j),'.asim'];      
                    end
                    files_to_run{i,j} = save_file_str;

                    %Write text to the file name specified, line by line
                    fid = fopen(save_file_str, 'w');        
                    for k=1:obj.sim_file_length
                        try fprintf(fid, '%s \n',new_sim_file_text{k,:});
                        catch
                            if ischar(obj.sims_folder)
                                error(['Error writing to .asim file. Ensure ',obj.sims_folder,' exists.'])
                            elseif iscell(obj.sims_folder)
                                error(['Error writing to .asim file. Ensure ',obj.sims_folder{1},' exists.'])
                            end
                        end
                    end        
                    fclose(fid);
                end
            end
            
            %Now we run the simulations
            if obj.to_parallelize
                simulation_data = cell(size(files_to_run));
                column_headers = cell(size(files_to_run));
                sim_fol_cell = obj.sims_folder;
                dat_file = obj.sim_output_data_file;
                sour_folder = obj.source_folder;
                parfor i=1:obj.num_threads
                    sim_data_slice = cell(1,max(num_variations_vec));
                    col_head_slice = cell(1,max(num_variations_vec));
                    for j=1:num_variations_vec(i)
                        %Delete data from previous trials first
                        output = [sim_fol_cell{i},'\',dat_file,'.txt'];
                        if exist(output,'file') == 2
                            delete(output)
                        end
                        
                        file_to_run = files_to_run{i,j};
                        %Put together the string to call from the command line.
                        executable = ['"',sour_folder,'\AnimatSimulator" "',file_to_run,'"'];
                        
                        [status, message] = system(executable);

                        %Rename the file in order of calling
                        if status
                            warning('Simulation has failed to run. Examine values and boundaries.');
                            error(message)
                        else
                            new_name = [sim_fol_cell{i},'\',dat_file,'_',num2str(j),'.txt'];
                            [renamed,~] = movefile(output,new_name);
                            if ~renamed
                                error('Simulation output file not found. Ensure that sim_output_data_file and sims_folder are passed properly.');
                            end
                            %Save the data to send to the user
                            data_struct = importdata(new_name);
                            if isempty(data_struct)
                                error('Data struct is empty. Fix your chart')
                            end
                            sim_data_slice{j} = data_struct.data;
                            try col_head_slice{j} = data_struct.colheaders;
                            catch
                                warning('No column headers. Using column headers from previous simulation. This is probably because the simulation blew up')
                                col_head_slice{j} = col_head_slice{j-1};
                            end
                        end
                        
                    end
%                     simulation_data(i,1:num_variations_vec(i)) = sim_data_slice;
%                     column_headers(i,1:num_variations_vec(i)) = col_head_slice;
                    simulation_data(i,:) = sim_data_slice;
                    column_headers(i,:) = col_head_slice;
                end %end parfor
                simulation_data = reshape(simulation_data',[],1);
                column_headers = reshape(column_headers',[],1);
                
                simulation_data = simulation_data(~cellfun(@isempty,simulation_data));
                column_headers = column_headers(~cellfun(@isempty,column_headers));
            else
                simulation_data = cell(num_variations,1);
                column_headers = cell(num_variations,1);
                files_to_run = files_to_run(:);
                for i=1:num_variations                
                    %Delete data from previous trials first
                    output = [obj.sims_folder,'\',obj.sim_output_data_file,'.txt'];
                    if exist(output,'file') == 2
                        delete(output)
                    end
                    
                    %Put together the string to call from the command line.
                    executable = ['"',obj.source_folder,'\AnimatSimulator" "',files_to_run{i},'"'];
                    [status, message] = system(executable);

                    %Rename the file in order of calling
                    if status
                        warning('Simulation has failed to run. Examine values and boundaries.');
                        error(message)
                    else
                        new_name = [obj.sims_folder,'\',obj.sim_output_data_file,'_',num2str(i),'.txt'];
                        [renamed,~] = movefile(output,new_name);
                        if ~renamed
                            error('Simulation output file not found. Ensure that sim_output_data_file and sims_folder are passed properly.');
                        end
                        %Save the data to send to the user
                        data_struct = importdata(new_name);
                        simulation_data{i} = data_struct.data;
                        column_headers{i} = data_struct.colheaders;
                    end

                    %Print a simple code to tell the user how many trials have
                    %been run in this batch. "-" means incomplete, "+" means
                    %complete.
                    progress_string = [repmat('+',1,i),repmat('-',1,num_variations-i)];
                    backspace_string = repmat('\b',1,num_variations);
                    fprintf([backspace_string,'%s'],progress_string);                
                end
                fprintf('\n');
            end
            
            obj.clean_sims_folder();
        end
        
        function success = set_bounds(obj,new_bounds)
            if isequal(size(new_bounds),size(obj.animatlab_bounds))
                if all(new_bounds(:,1) >= obj.animatlab_bounds(:,1)) &&...
                        all(new_bounds(:,2) <= obj.animatlab_bounds(:,2))
                    obj.bounds = new_bounds;
                    success = true;
                else
                    success = false;
                    warning('New boundaries are not within those set by AnimatLab. Bounds will not be changed.')
                end
            else
                success = false;
                warning('New boundaries are not the correct size. Bounds will not be changed.')
            end
        end
        
        function success = set_lin_con(obj,lin_con)
            if iscell(lin_con)
                if length(lin_con) == 2
                    A = lin_con{1};
                    b = lin_con{2};
                    if size(A,1) == size(b,1) && size(b,2) == 1 &&...
                            size(A,2) == size(obj.optimization_variables,1)
                        obj.linear_constraints = {A,b};
                        success = true;
                    else
                        warning('Linear constraints are not the correct size.')
                        success = false;
                    end
                else
                    warning('Linear constraints should be a 2x1 cell array.')
                    success = false;
                end
            else
                success = false;
                warning('Linear constraints should be a 2x1 cell array.')
            end
        end
        
        function success = set_plot_time_limits(obj,time_limits)
            if length(time_limits) == 2 && time_limits(2) > time_limits(1)
                obj.plot_time_limits = time_limits;
                if isempty(obj.time_vec)
                    warning('A simulation will be run before the time limits can be properly set.')
                    obj.need_to_set_plot_time_limits = true;
                    %obj.vary_params_run_sims(obj.initial_values);
                    success = false;
                else
                    obj.need_to_set_plot_time_limits = false;
                    obj.plot_time_indices(1) = find(obj.time_vec >= time_limits(1),1,'first');
                    obj.plot_time_indices(2) = find(obj.time_vec < time_limits(2),1,'last');
                    success = true;
                end
            else
                success = false;
                warning('Plot time limits must be a 2-element, nondecreasing vector.')
            end
        end
        
        function success = clean_sims_folder(obj)
            if obj.to_parallelize
                for i=1:length(obj.sims_folder)
                    delete([obj.sims_folder{i},'\*.asim']);
                    delete([obj.sims_folder{i},'\*.txt']);
                end
            else
                delete([obj.sims_folder,'\*.asim']);
                delete([obj.sims_folder,'\*.txt']);
            end
            success = true;
        end
        
        function [data_cell_eval,col_headers] = run_simulations(obj,x)
            %We pass x to vary_params_run_sims to evaluate the simulation.
            %However, we need to make sure we do not try to evaluate
            %columns of x that are outside our bounds; AnimatLab will
            %crash.
            [n_params,n_trials] = size(x);
            if n_params ~= length(obj.bounds(:,1))
                error('Passed parameter vector is not the proper length.')
            end
            obj.inds_within_bounds = [];
            obj.inds_outside_bounds = [];
            for i=1:n_trials
                out_of_bounds = ((x(:,i) < obj.bounds(:,1)) | (x(:,i) > obj.bounds(:,2)));
                if any(out_of_bounds)
                    obj.inds_outside_bounds = [obj.inds_outside_bounds,i];
                    out_of_bounds_inds = find(out_of_bounds);
                    for j=1:length(out_of_bounds_inds)
                        warning(['For parameter values ',num2str(i),', parameter ',num2str(out_of_bounds_inds(j)),' is outside bounds.']);
                    end
                else
                    obj.inds_within_bounds = [obj.inds_within_bounds,i];
                end
            end
            
            %Call AnimatLab for the columns of x that are within the bounds
            [data_cell_eval,col_headers] = obj.vary_params_run_sims(x(:,obj.inds_within_bounds));
        end
        
        function objective = objective_function(obj,x,obj_func_num)
            %x - the matrix of system parameters to evaluate. Each column
            %is a separate set, and the rows correspond to
            %obj.optimization_variables
            %obj_func_num - which objective function to evaluate
            [data_cell_eval,new_col_headers] = obj.run_simulations(x);
            obj.col_headers = new_col_headers;
            
            n_trials = size(x,2);
            
            if size(obj_func_num,1) > 1
                obj_func_num = obj_func_num';
            end
            
            %We will need to return a matrix of NaNs for columns of x that
            %are outside the boundaries. To do this, we need to know the
            %output size. As soon as we get one successful AnimatLab run,
            %save the size of the output.
            if ~isempty(obj.inds_within_bounds) && isempty(obj.output_data_size)
                obj.output_data_size = size(data_cell_eval{obj.inds_within_bounds(1)});                
            end
            
            %Also save the time vector, so we can still use our
            %interpolation inside the objective function.
            if ~isempty(obj.inds_within_bounds) && isempty(obj.time_vec)
                obj.time_vec = data_cell_eval{obj.inds_within_bounds(1)}(:,2);
                if obj.need_to_set_plot_time_limits
                    obj.set_plot_time_limits(obj.plot_time_limits);
                end
            end
            
            %For each column of x that did not evaluate, replace that index
            %of the data_cell with NaN.
            if isempty(obj.inds_outside_bounds)
                data_cell = data_cell_eval;
            else
                data_cell = cell(n_trials,1);
                data_cell(obj.inds_within_bounds) = data_cell_eval;
                for i=obj.inds_outside_bounds
                    error_data = NaN(obj.output_data_size);
                    error_data(:,2) = obj.time_vec;
                    data_cell{i} = error_data;
                end
            end

            if length(obj_func_num)>1
                objective = cell(length(obj_func_num),1);
                for i = obj_func_num
                    try objective{i} = feval(obj.user_objective_function{i},data_cell,new_col_headers,obj.desired_output);
                    catch ME
                        if strcmp(ME.identifier,'MATLAB:UndefinedFunction') && contains(ME.message,obj.user_objective_function{obj_func_num})
                            error('Function "%s%s" not found on the path. Add this function to the path, or create a function with this name.',obj.user_objective_function,'.m');
                        else
                            error(ME.message)
                        end
                    end
                end
            elseif length(obj_func_num)==1
                if ischar(obj.user_objective_function)
                    try objective = feval(obj.user_objective_function,data_cell,new_col_headers,obj.desired_output);
                    catch ME
                        if strcmp(ME.identifier,'MATLAB:UndefinedFunction') && contains(ME.message,obj.user_objective_function{obj_func_num})
                            error('Function "%s%s" not found on the path. Add this function to the path, or create a function with this name.',obj.user_objective_function,'.m');
                        else
                            error(ME.message)
                        end
                    end
                elseif iscell(obj.user_objective_function)
                    try objective = obj.user_objective_function{obj_func_num}(data_cell,new_col_headers,obj.desired_output);
                    catch ME
%                         if strcmp(ME.identifier,'MATLAB:UndefinedFunction') && contains(ME.message,obj.user_objective_function{obj_func_num})
%                             error('Function "%s%s" not found on the path. Add this function to the path, or create a function with this name.',obj.user_objective_function{obj_func_num},'.m');
%                         else
%                             error(ME.message)
%                         end
                        error(ME.message)
                    end
                end
            end
        end
        
        function success = plot_comparison(obj)
            if isempty(obj.final_values)
                x = obj.initial_values;
                legend_string = 'Initial';
            else
                x = obj.final_values;
                legend_string = 'Final';
            end
            
            data_cell = obj.run_simulations(x);
            if isempty(data_cell)
                warning('Initial values are outside the boundaries.')
                success = false;
            else
                data = data_cell{1};

                for i=3:size(data,2)
                    figure
                    clf
                    hold on
                    grid on
                    plot(data(:,2),data(:,i),'Linewidth',2);
                    if ~isempty(obj.desired_output)
                        plot(obj.desired_output(:,1),obj.desired_output(:,i-1),'r','Linewidth',2);                
                    end
                    legend(legend_string,'Desired');
                    xlabel('time')
                    title(['Comparison for data column ',num2str(i)])
                end
                success = true;
            end
        end
        
        function data_cell = scan_parameter(obj,variable_index,variable_values,objective_function_to_eval)
            [num_indices,num_values] = size(variable_values);
            if any(variable_index > length(obj.initial_values))
                error('Desired parameter index does not exist.')
            end
            if length(variable_index) ~= num_indices
                error('Desired parameters are not the correct size.')
            end
            temp_values = repmat(obj.initial_values,1,num_values);
            temp_values(variable_index,1:num_values) = variable_values;
            
            if objective_function_to_eval
                data_cell = obj.objective_function(temp_values,objective_function_to_eval);
                
                obj.scan_parameter_data{variable_index(1)} = data_cell;
              
            else
                [data_cell,~] = obj.run_simulations(temp_values);
                obj.scan_parameter_data{variable_index(1)} = data_cell;
            
            end
        end
        
        function success = write_to_aproj(obj,params)
            if ~isequal(size(params),[size(obj.optimization_variables,1),1])
                error('Input properties must be a column vector.')
            end
            
            property_cell = obj.optimization_variables(:,2:3);
            for i=1:length(params)
                property_cell{i,3} = num2str(params(i)*obj.optimization_variables{i,6});
            end
            
            obj.update_sim_file(property_cell)
            
            success = true;
        end
        
        function success = apply_all_params(obj)
            
            props = obj.optimization_variables(:,2:3);
            
            if isempty(obj.final_values)
                values = obj.initial_values;
            else
                values = obj.final_values;
            end
            
            for i=1:size(props,1)
                props{i,3} = num2str(values(i));
            end
            
            obj.update_sim_file(props);
            success = true;
        end
        
        function written_file = update_sim_file(obj, info_cell_array)

            fileID = fopen(obj.aproj_file);
            cell_proj_file = textscan(fileID,'%s', 'delimiter','\n');
            cell_proj_file = cell_proj_file{1};
            fclose(fileID);

            size_info = size(info_cell_array);
            size_info = size_info(1);
            row = 1;

            while row <= size_info
        %         disp(['processing row ' num2str(row)]);
                % get the right id for the given object name
                [prop_to_find, spec_info] = obj.identify_property(info_cell_array{row,2});
                if ~strcmp(prop_to_find , 'Error')
                    spec_id = obj.find_id(info_cell_array{row,1});
                    if ~strcmp(spec_id, 'Error')
                        %with valid id + property name, process the value (check range
                        % + scale)
                        [val, sca, act, error] = obj.process_numerical(info_cell_array{row,3}, prop_to_find);
                        if ~error
                            % if the numerical processing doesn't throw an error:
                            % make the changes to the file for item id, property,
                            % value, scale, actual
                            if spec_info == 1
                                disp(['[object] ' info_cell_array{row,1} ...
                                    ' [id] ' spec_id ...
                                    ' [property] m' prop_to_find ...
                                    ' [val/sca/act] ' num2str(val) '/' sca '/' num2str(act)]);
                            elseif spec_info == 2
                                disp(['[object] ' info_cell_array{row,1} ...
                                    ' [id] ' spec_id ...
                                    ' [property] h' prop_to_find ...
                                    ' [val/sca/act] ' num2str(val) '/' sca '/' num2str(act)]);
                            elseif spec_info == 3
                                %This codes for muscle damping, which is
                                %confusing because 'B' is used both in the
                                %stimulus-tension curve, and for muscle
                                %damping. Therefore we have a special flag
                                %for it.
                                %disp('damping')
                            else
                                disp(['[object] ' info_cell_array{row,1} ...
                                    ' [id] ' spec_id ...
                                    ' [property] ' prop_to_find ...
                                    ' [val/sca/act] ' num2str(val) '/' sca '/' num2str(act)]);
                            end
                            cell_proj_file = obj.set_info(spec_id, prop_to_find, spec_info, val, sca, act, cell_proj_file);
                        end
                    else
                        disp(['[ERROR] No ID found for [object] ' info_cell_array{row,1}]);
                    end
                else
                    disp(['[ERROR] Invalid property for [object] ' info_cell_array{row,1} ...
                        ' [property] ' info_cell_array{row,2}]);
                end
                row = row + 1;

            end
            % write the new file to disk with the old data + changes
            fid = fopen([obj.aproj_file(1:length(obj.aproj_file)-6) '_mod.aproj'], 'wt');
            % celldisp(cell_lengthmap_file);
            fprintf(fid, '%s\n' , cell_proj_file{:});
            fclose(fid);

            written_file = [obj.aproj_file(1:length(obj.aproj_file)-6) '_mod.aproj'];
        end

        function full_id = find_id(obj, object_name)
        %     disp(['[object name] ' object_name]);
            full_id = 'Error';
            % while there are lines to lookup...
            i = 1;
%             size_info = size(obj.sim_file_text);
%             size_info = size_info(1);
            found_flag = 0;
            while ~found_flag && i <= obj.sim_file_length
                % if the current line is long enough to have a name...
                curr_line = obj.sim_file_text{i};
                if (length(curr_line)> length('<Name></Name>') && strncmpi(curr_line,'<Name>',6)) ||...
                        (length(curr_line)> length('<ModuleName></ModuleName>') && strncmpi(curr_line,'<ModuleName>',12))
                    % disp(['[name_found] ' curr_line]);
                    short_name = curr_line(7:length(curr_line)-7);
                    short_name2 = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
                    if (length(curr_line)> length('<ModuleName></ModuleName>'))
                        short_name2 = curr_line(13:length(curr_line)-13);
                    end
                    % disp(['[short_name] ' short_name ' vs. [input] ' object_name]);
                    % if the name is correct...
                    if strcmp(object_name,short_name) || strcmp(object_name,short_name2)
                        % now to find the id
                        % disp('correct name found');
                        %process backwards to the opening of the object tag
                        % (open tag w/o data)
                        object_start_flag = 0;
                        while(~object_start_flag && i>0)
                            curr_line = obj.sim_file_text{i};
                            num_open_tags = length(strfind(curr_line,'<'));
                            num_close_tags = length(strfind(curr_line,'>'));
                            num_slash = length(strfind(curr_line,'/'));
                            if (length(curr_line)> length('<>') && num_open_tags == 1 ...
                                    && num_close_tags == 1  && num_slash == 0)
                                % if the current line has just a tag
                                % disp(['[object type] ' curr_line(2:length(curr_line)-1)]);
                                object_start_flag = 1;
                            else
                                i = i -1;
                            end
                        end
                        % then move down until an <ID> is found
                        links_flag = 0;
                        while ~found_flag && i<length(obj.sim_file_text) && length(curr_line)>4 && (links_flag || ~strncmpi(curr_line,'<ID>',4))
                            curr_line = obj.sim_file_text{i};
                            if strncmpi(curr_line,'<InLinks>',length('<InLinks>')) || strncmpi(curr_line,'<OutLinks>',length('<OutLinks>'))
                                links_flag = 1;
                            elseif strncmpi(curr_line,'</InLinks>',length('</InLinks>')) || strncmpi(curr_line,'</OutLinks>',length('</OutLinks>'))
                                links_flag = 0;
                            else
                                % otherwise, we have a valid id
                                if length(curr_line) > length('<ID></ID>') && strncmpi(curr_line,'<ID>',4)
                                    id_line = curr_line;
                                    full_id = id_line(5:length(id_line)-5);
                                    found_flag = 1;
                                end
                            end

                            i = i+1;
                        end
                    end
                end
                i = i+1;
            end
        end

        function [value, scale, actual, error] = process_numerical(obj, actual, property)
            actual_check = str2double(actual);
            if isnan(actual_check)
                value = actual;
                scale = [];
                error = 0;        
            else
                actual = actual_check;
                value = num2str(0);
                scale = 'None';
                error = 0;
                if ischar(property)
%                     available_properties = load(prop_file);
%                     prop_set = available_properties.Properties;
                    % lookup the property in the animatlab file
                    for i = 1:length(obj.animatlab_properties)
                        current_page = obj.animatlab_properties{i,1};
                        size_info = size(current_page,1);
                    end
                end
                % disp(['[actual] ' actual]);
                if actual == 0
                    value = num2str(0);
                    scale = 'None';
                else
                    minor_count = 0;
                    temp_act = actual;
                    if abs(temp_act) > 1000
                        while abs(temp_act)>1000
                            temp_act = temp_act/1000;
                            minor_count = minor_count + 1;
                        end
                        value = num2str(temp_act);
                        if minor_count == 0
                            scale = 'None';
                        elseif minor_count == 1
                            scale = 'kilo';
                        elseif minor_count == 2
                            scale = 'mega';
                        elseif minor_count == 3
                            scale = 'giga';
                        elseif minor_count == 4
                            scale = 'tera';
                        else
                            scale = 'Error';
                        end
                    elseif abs(temp_act) <.1
                        while abs(temp_act)<.1
                            temp_act = temp_act*1000;
                            minor_count = minor_count + 1;
                        end
                        value = num2str(temp_act);
                        if minor_count == 0
                            scale = 'None';
                        elseif minor_count == 1
                            scale = 'milli';
                        elseif minor_count == 2
                            scale = 'micro';
                        elseif minor_count == 3
                            scale = 'nano';
                        elseif minor_count == 4
                            scale = 'pico';
                        else
                            scale = 'Error';
                        end
                    else
                        scale = 'None';
                        value = actual;
                    end
                end
            end
        end

        function [prop_to_find,special_info] = identify_property(obj, lookup_string)
            if strncmpi(lookup_string,'m',1)
                special_info = 1;
            elseif strncmpi(lookup_string,'h',1)
                special_info = 2;
            elseif strncmpi(lookup_string,'damping',7)
                special_info = 3;
            else
                special_info = 0;
            end
            prop_to_find = 'Error';
            % lookup the property in the animatlab file
            for i = 1:length(obj.animatlab_properties)
                current_page = obj.animatlab_properties{i,1};
                size_info = size(current_page,1);
                for j = 1:size_info % the length of the cell
                    if strcmp(current_page{j,1},lookup_string)
                        prop_to_find = current_page{j,4};
                        %fprintf('prop_to_find: %s',prop_to_find);
                        return;
                    end
                end
            end
        end
        
        function success = display_variable_scale(obj) 
            
            fprintf('\n***** SCALE FOR VARIABLES (none implies a scale of 1) *****\n')
            for i=1:size(obj.optimization_variables,1)
                
                for j=[1,2,3,6]
                    fprintf('%s',obj.optimization_variables{i,j})
                    num_tab = ceil((24-length(obj.optimization_variables{i,j}))/4);
                    for k=1:num_tab
                        fprintf('\t')
                    end
                end
                fprintf('\n')
            end
            success = true;
        end
        
        function success = save_all_figures(obj)
            cur_time = datestr(clock,30);
            figure_directory = [obj.performance_folder,'\',cur_time];
            warning(['Saving all figures to ',figure_directory]);
            mkdir(figure_directory)
            h = get(0,'children');
            for i=1:length(h)
                savefig(h(i), [figure_directory,'\figure',num2str(i)]);
            end
            success = true;
        end
        
        function success = save_instance(obj)
            cur_time = datestr(clock,30);
            save(['tune_instance_',cur_time],'obj');
            success = true;
        end
        
        function success = set_initial_values(obj,init_vals)
            if ~isequal(size(init_vals),size(obj.bounds(:,1)))
                error('Initial values must be the proper size.')
            end
            if isvector(init_vals) && all(init_vals >= obj.bounds(:,1)) && all(init_vals <= obj.bounds(:,2))
                obj.initial_values = init_vals;
                success = true;
            else
                success = false;
            end
        end
        
        function success = set_final_values(obj,fin_vals)
            if isvector(fin_vals) && all(fin_vals >= obj.bounds(:,1)) && all(fin_vals <= obj.bounds(:,2))
                obj.final_values = fin_vals;
                success = true;
            else
                success = false;
            end
        end
        function all_objective_array = out_of_memory_data_study(obj,objective_func_num)
            %This function was written to analyze data that was recorded by
            %not analyed because of an out of memory error (or any error).
            %It should not be called by any other function
            current_sim_attempt = 1;
            for j = 1:obj.num_threads
                still_finding = 1;
                current_file_number = 1;
                while still_finding == 1
                    new_filename = [obj.sims_folder{j},'\',obj.sim_output_data_file,'_',num2str(current_file_number),'.txt'];
                    try
                        new_data_struct = importdata(new_filename);
                    catch
                        if j ~= obj.num_threads
                            fprintf('Simulation attempt #%d not found in %s. Moving to %s\n', current_sim_attempt, obj.sims_folder{j}, obj.sims_folder{j+1})
                        else
                            fprintf('Simulation attempt #%d not found in %s. No more threads to look in, so no more data to look for\n', current_sim_attempt, obj.sims_folder{j})
                        end
                        still_finding = 0;
                        break
                    end
                    new_data{1} = new_data_struct.data;
                    if length(objective_func_num)>1
                        objective_current = cell(length(objective_func_num),1);
                    end
                    if length(objective_func_num)>1
                        for k = objective_func_num
                            objective_current{k} = feval(obj.user_objective_function{k},new_data,obj.desired_output);
                        end
                    elseif length(objective_func_num)==1
                        objective_current = feval(obj.user_objective_function{objective_func_num},new_data,obj.desired_output);
                    end
                    all_objective{current_sim_attempt} = objective_current;
                    current_sim_attempt = current_sim_attempt+1;
                    current_file_number = current_file_number +1;
                end
            end
            all_objective_array = inf(current_sim_attempt-1,3);
            for i = 1:current_sim_attempt-1
                try all_objective_array(i,:) = cell2mat(all_objective{i});
                catch
                    warning('Simulation #%d was not analyzed. Leaving data as Inf')
                end
            end
        end
    end %end methods
    
    methods(Static)
        function file_with_edit = set_info(full_id, property_name, modifier, value, scale, actual, celled_proj_file)    
            % Test
            % find the correct line by linear scan
            i = 1;
            file_with_edit = [];
            %celldisp(celled_lengthmap_file);
            replaced = 0;
            size_info = size(celled_proj_file,1);

            m_mod_flag = 0;
            h_mod_flag = 0;
            skip_entry = 0;
            if modifier == 1
                m_mod_flag = 1;
            elseif modifier == 2
                h_mod_flag = 1;
            elseif modifier == 3
                skip_entry = 1;
            end
            while(i < size_info && ~replaced)
                if ischar(celled_proj_file{i}) && length(celled_proj_file{i}) > length('<ID></ID>')...
                        && strncmpi(celled_proj_file{i},'<ID>',4)

                    %identify the ID, if this line has one.
                    to_compare = celled_proj_file{i};
                    to_compare = to_compare(5:length(to_compare)-5);
                    % if the correct ID is found
                    if strcmp(to_compare,full_id)
                        links_flag = 0;
                        caA_m_flag = 0;
                        caD_h_flag = 0;
                        i = i+1;
                        % cycle through the properties until it hits the next id
                        curr_line = celled_proj_file{i};

                        while i<length(celled_proj_file) && length(curr_line)>4 && (links_flag || ~strncmpi(curr_line,'<ID>',4))
                            if (strncmpi(curr_line,'<InLinks>',length('<InLinks>')) ...
                                    || strncmpi(curr_line,'<OutLinks>',length('<OutLinks>')) ...
                                    || strncmpi(curr_line,'<CaActivation>',length('<CaActivation>'))...
                                    || strncmpi(curr_line,'<CaDeactivation>',length('<CaDeactivation>'))...
                                    || strncmpi(curr_line,'<Gain>',length('<Gain>'))...
                                    || strncmpi(curr_line,'<LengthTension>',length('<LengthTension>'))...
                                    || strncmpi(curr_line,'<StimulusTension>',length('<StimulusTension>')));
                                links_flag = 1;
                            end

                            if (strncmpi(curr_line,'<CaActivation>',length('<CaActivation>')))
                                caA_m_flag = 1;
                            elseif (strncmpi(curr_line,'<CaDeactivation>',length('<CaDeactivation>')))
                                caD_h_flag = 1;
                            elseif (strncmpi(curr_line,'</CaActivation>',length('</CaActivation>')))
                                caA_m_flag = 0;
                            elseif (strncmpi(curr_line,'</CaDeactivation>',length('</CaDeactivation>')))
                                caD_h_flag = 0;
                            end
                            if (strncmpi(curr_line,'</InLinks>',length('</InLinks>')) ...
                                    || strncmpi(curr_line,'</OutLinks>',length('</OutLinks>'))...
                                    || strncmpi(curr_line,'</CaActivation>',length('</CaActivation>'))...
                                    || strncmpi(curr_line,'</CaDeactivation>',length('</CaDeactivation>'))...
                                    || strncmpi(curr_line,'</Gain>',length('</Gain>'))...
                                    || strncmpi(curr_line,'</LengthTension>',length('</LengthTension>'))...
                                    || strncmpi(curr_line,'</StimulusTension>',length('</StimulusTension>')));
                                links_flag = 0;
                            end

                            if length(curr_line)>length(property_name)+length('</>') && strncmpi(curr_line,['<' property_name],length(property_name)+1)
                                if skip_entry
                                    %do nothing

                                    %disp('Doing nothing!')
                                    skip_entry = 0;
                                else

                                    % if the property is found, read/write the property value
                                    comp_line3 = curr_line(length(curr_line)-1:length(curr_line));
                                    % swap out the info in the cell array
                                    if ((m_mod_flag && caA_m_flag) || (h_mod_flag && caD_h_flag) || ...
                                            (~m_mod_flag && ~h_mod_flag && ~caA_m_flag && ~caD_h_flag))
                                        if strcmp(comp_line3,'/>')
                                            % then the files are embedded in the tag, and look
                                            % for the beginning of the value data field
                                            start_index = strfind(curr_line,'Value="');
                                            start_index = start_index(1)+length('Value="');
                                            % (current line up through value=") + value +
                                            % ' Scale="' + scale + ' Actual="' + actual + '"/>'
                                            %disp(['[value value] ' value]);

                                            new_string = [curr_line(1:start_index-1) num2str(value) '" Scale="' scale '" Actual="' num2str(actual) '"/>'];
                                            celled_proj_file{i} = new_string;
                                            file_with_edit = celled_proj_file;
                                            replaced = 1;
                                            break;
                                        else
                                            %We have a nonstandard property. These
                                            %are usually booleans, which have a
                                            %different format in the .aproj files
                                            new_string = ['<',property_name,'>',value,'</',property_name,'>'];
                                            celled_proj_file{i} = new_string;
                                            file_with_edit = celled_proj_file;
                                            replaced = 1;
                                            break;

                                        end
                                    end
                                end
                            else
                                %Do nothing
                            end

                            i = i+1;
                            curr_line = celled_proj_file{i};
                        end
                    end
                end
                i = i + 1;
            end
            if isempty(file_with_edit)
                error(['The property "',property_name,'" may not exist within the simulation. Please add it to the simulation, save it, and export another standalone simulation.'])
            end
        end
        
        function getl_data_file_text = read_text_file(file_to_read)
            try fileID = fopen(file_to_read,'r');
            catch
                error(['File to read: "',file_to_read,'" is nonexistent or empty']);
            end
            getl_data_file_text = cell(1e6,1);
            j = 1;
            while ~feof(fileID)
                getl_data_file_text{j} = fgetl(fileID);
                j = j + 1;
            end
            getl_data_file_text = getl_data_file_text(1:j-1);
            
        end
    end
    
end %end class

