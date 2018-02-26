close all
clear all %#ok<CLALL>
clc


simFile = 'TryAgain_Standalone.asim';

% parallelize! w/ cell array
% simsFolder = {  'E:\GitHub\Animatlab\SNS\hw2\SimFiles\Thread1',...
%                 'E:\GitHub\Animatlab\SNS\hw2\SimFiles\Thread2',...
%                 'E:\GitHub\Animatlab\SNS\hw2\SimFiles\Thread3',...
%                 'E:\GitHub\Animatlab\SNS\hw2\SimFiles\Thread4'};   

simsFolder = 'E:\GitHub\Animatlab\SNS\hw2\SimFiles\Thread1';
                
performanceFolder = 'E:\GitHub\Animatlab\SNS\hw2\Performance';

% location of animatlab2 binary (.exe)
sourceFolder = 'C:\Program Files (x86)\NeuroRobotic Technologies\AnimatLab\bin';

% userObjectiveFunction = {'percentOvershoot', 'percentOvershootMat', 'plotResponse'};
userObjectiveFunction = {@range};


% name of the graph to export every time
simOutputDataFile = 'DataTool_SimOutput';

% string property_type, string id, string property_name
% see list in Tune_animatlab line 150
variablesCell = {   'neuron', 'Range of Motion 2', 'TonicStimulus';...
                    % 'nonspikingsynapse','Dep Add','SynAmp';...
                    % 'nonspikingsynapse','Hyp Sub','SynAmp';...
                    % 'neuron','Comm. Velocity','TimeConst';...
                    'neuron','CPG Speed 2','TonicStimulus'};
                    
                
desiredOutputFile = [];
tune = Tune_animatlab(simFile,variablesCell,desiredOutputFile,simOutputDataFile,userObjectiveFunction,simsFolder,performanceFolder,sourceFolder);

%Call the objective functions to make sure they aren't broken.
% selector number is the last number (choosing which objective function)
output1 = tune.objective_function(tune.initial_values,1);
% output2 = tune.objective_function(tune.initial_values,2);
% output3 = tune.objective_function(tune.initial_values,3);

%% Sweep parameter values to see how they affect the objective function output.
numK = 11;
numStim = 4;

R = 20;
kSyn = 1;

ROM_stim = linspace(0,R,numK);

%Put the parameters that we want to sweep in a matrix. Each column is
%another set to test.

%Change the synaptic gain
% gVals = [ROM_stim];
gScan = tune.scan_parameter(1:1,[ROM_stim],1);

%Plot the results. Because this is not a linear system, multiple different
%values will be recorded for the same parameters. Therefore, plot each
%point separately.
gFig = figure;
subplot(1,1,1)
title('ROM Input vs. Output');
hold on
xlabel('ROM Input (% V above rest)')
ylabel('ROM Out (% V)')

hold on

x = gScan(:,1);
y = gScan(:,2);

p = polyfit(x, y, 1);
x1 = linspace(0,1);
y1 = polyval(p,x1);

for i=1:numK
    for j=1:4
        subplot(1,1,1)
        plot(x, y,'o')
        plot(x1, y1)
    end
end

tune.save_all_figures;

close all
