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
userObjectiveFunction = {@plotResponse};


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
gVals = [ROM_stim];
gScan = tune.scan_parameter(1:1,gVals,1);

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
        % I don't know what's going on here, but it runs until here
        plot(ROM_stim(i),gScan{1,i}(j),'o')
        
        subplot(2,1,2)
        plot(ROM_stim(i),gScan{2,i}(j),'o')
    end
end

% tcFig = figure;
% subplot(2,1,1)
% hold on
% ylabel('percent overshoot (%)')
% subplot(2,1,2)
% hold on
% xlabel('\tau_{Comm. Velocity} (ms)')
% ylabel('rise time (s)')
% 
% hold on
% for i=1:numK
%     for j=1:4
%         subplot(2,1,1)
%         plot(velTC(i),tcScan{1,i}(j),'o')
%         
%         subplot(2,1,2)
%         plot(velTC(i),tcScan{2,i}(j),'o')
%     end
% end

tune.save_all_figures;

close all
