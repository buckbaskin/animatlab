close all
clear all %#ok<CLALL>
clc


simFile = 'TryAgain_Standalone.asim';

% parallelize! w/ cell array
% TODO(buckbaskin): change this to match E:/...
simsFolder = {  'C:\Users\nszczeci\Documents\SimFiles\Thread1',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread2',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread3',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread4'};   

% simsFolder = 'C:\Users\nszczeci\Documents\SimFiles\Thread1';
                
% TODO(buckbaskin): change this to match E:/...
performanceFolder = 'C:\Users\nszczeci\Documents\Performance';

% location of animatlab2 binary (.exe)
sourceFolder = 'C:\Program Files (x86)\NeuroRobotic Technologies\AnimatLab\bin';

userObjectiveFunction = {   'percentOvershoot','percentOvershootMat','plotResponse'};

% name of the graph to export every time
simOutputDataFile = 'DataTool_2';

% string property_type, string id, string property_name
% see list in Tune_animatlab line 150
variablesCell = {   'nonspikingsynapse','Dep Add','SynAmp';...
                    'nonspikingsynapse','Hyp Sub','SynAmp';...
                    'neuron','Comm. Velocity','TimeConst';...
                    'neuron','Comm. Position','TonicStimulus'};
                    
                
desiredOutputFile = [];
tune = Tune_animatlab(simFile,variablesCell,desiredOutputFile,simOutputDataFile,userObjectiveFunction,simsFolder,performanceFolder,sourceFolder);

%Call the objective functions to make sure they aren't broken.
% selector number is the last number (choosing which objective function)
output1 = tune.objective_function(tune.initial_values,1);
output2 = tune.objective_function(tune.initial_values,2);
output3 = tune.objective_function(tune.initial_values,3);

%% Sweep parameter values to see how they affect the objective function output.
numK = 11;
numStim = 4;

R = 20;
kSyn = 1;

delEadd = 220;
delEsub = -40;

% from slides last time (class 1/29)
depAddGbaseline = kSyn*R./(delEadd - kSyn*R);
hypSubGbaseline = delEadd/delEsub*-depAddGbaseline;

depAddG = linspace(depAddGbaseline,10*depAddGbaseline,numK);
hypSubG = linspace(hypSubGbaseline,10*hypSubGbaseline,numK);

%Put the parameters that we want to sweep in a matrix. Each column is
%another set to test.

%Change the synaptic gain
gVals = [depAddG;hypSubG];
gScan = tune.scan_parameter(1:2,gVals,1);

%Change the velocity neuron's time constant
velTC = linspace(5,100,numK);
tcScan = tune.scan_parameter(3,velTC,1);

%Plot the results. Because this is not a linear system, multiple different
%values will be recorded for the same parameters. Therefore, plot each
%point separately.
gFig = figure;
subplot(2,1,1)
hold on
ylabel('percent overshoot (%)')
subplot(2,1,2)
hold on
xlabel('g_{add} (\muS)')
ylabel('rise time (s)')

hold on
for i=1:numK
    for j=1:4
        subplot(2,1,1)
        plot(depAddG(i),gScan{1,i}(j),'o')
        
        subplot(2,1,2)
        plot(depAddG(i),gScan{2,i}(j),'o')
    end
end

tcFig = figure;
subplot(2,1,1)
hold on
ylabel('percent overshoot (%)')
subplot(2,1,2)
hold on
xlabel('\tau_{Comm. Velocity} (ms)')
ylabel('rise time (s)')

hold on
for i=1:numK
    for j=1:4
        subplot(2,1,1)
        plot(velTC(i),tcScan{1,i}(j),'o')
        
        subplot(2,1,2)
        plot(velTC(i),tcScan{2,i}(j),'o')
    end
end

tune.save_all_figures;

close all

%% Define an objective function to optimize, and use optimization to obtain the desired performance.

paramVals = @(x) [.1*x(1);.55*x(1);x(2);0];
f = @(x) tune.objective_function(paramVals(x),2);
g = @(x) tune.objective_function(paramVals(x),3);

x0 = [1;5];
lb = [0,0];
ub = [10,200];

xf = fmincon( f,x0,[],[],[],[],lb,ub) %#ok<NOPTS>
f(xf)

options = optimoptions('fmincon');
options.FinDiffRelStep = eps^(1/4); % make this slightly bigger to avoid local minima
options.Display = 'iter';
options.StepTolerance = 1e-3;

xf = fmincon( f,x0,[],[],[],[],lb,ub,[],options) %#ok<NOPTS>
f(xf)
