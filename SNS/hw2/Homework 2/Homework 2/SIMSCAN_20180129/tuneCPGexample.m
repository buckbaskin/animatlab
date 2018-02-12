close all
clear all
clc


simFile = 'simpleCPG\simpleCPG_Standalone.asim';

simsFolder = { 'C:\Users\nszczeci\Documents\SimFiles\Thread1',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread2',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread3',...
                'C:\Users\nszczeci\Documents\SimFiles\Thread4'};   

% simsFolder = 'C:\Users\nszczeci\Documents\SimFiles\Thread1';
                

performanceFolder = 'C:\Users\nszczeci\Documents\Performance';
sourceFolder = 'C:\Program Files (x86)\NeuroRobotic Technologies\AnimatLab\bin';

userObjectiveFunction = {   'cpgEqV','cpgPeriod','cpgPeaks'};

simOutputDataFile = 'DataTool_1';

variablesCell = {   'neuron','Ext HC','mSlope';...
                    'neuron','Ext HC','hSlope';...
                    'neuron','Ext HC','hTimeConstant';...
                    'neuron','Flx HC','mSlope';...
                    'neuron','Flx HC','hSlope';...
                    'neuron','Flx HC','hTimeConstant';...
                    'nonspikingsynapse','Hyp IPSP CPG','SynAmp';...
                    'nonspikingsynapse','Hyp IPSP CPG 2','SynAmp';...
                    'neuron','CPG Speed','TonicStimulus';...
                    'stimulus','phaseStim','StartTime';...
                    'stimulus','phaseStim','EndTime';...
                    'stimulus','phaseStim','CurrentOn'};
                    
                
desiredOutputFile = [];
tune = Tune_animatlab(simFile,variablesCell,desiredOutputFile,simOutputDataFile,userObjectiveFunction,simsFolder,performanceFolder,sourceFolder);

xTuneEqV = @(x) [x;-x;500;x;-x;500;0;0;0;0;.001;0];
output1 = tune.objective_function(xTuneEqV(.045),1);

%% Obtain the desired plateau height
R = 20;
Er = -60;

fHt = @(x) (Er + R) - 1e3*tune.objective_function(xTuneEqV(x),1);
x1 = .01;
x2 = .1;
fHt(x1)
fHt(x2)
sl = fzero(fHt,[x1,x2])

%% Obtain the desired delta value
xTuneDelta = @(x) [sl;-sl;500;sl;-sl;500;x;0;0;0;.001;0];
fDelta = @(x) 1e3*tune.objective_function(xTuneDelta(x),1) - Er;
gf = fzero(fDelta,[1,1.5])

%% Show the delta also depends on stimulus current
xTuneDelta2 = @(x) [sl;-sl;500;sl;-sl;500;gf;0;x;0;.001;0];
fDelta2 = @(x) 1e3*tune.objective_function(xTuneDelta2(x),1) - Er;
numDrive = 11;
cpgDrive = linspace(0,20,numDrive);
deltaDrive = NaN(numDrive,1);
for i=1:numDrive
    deltaDrive(i) = fDelta2(cpgDrive(i));
end

figure
plot(cpgDrive,deltaDrive,'linewidth',2)
hold on
grid on
xlabel('CPG Drive (nA)')
ylabel('\delta (mV)')

%% Obtain the desired natural frequency
cpgDrive = 1;
xTunePeriod = @(x) [sl;-sl;x;sl;-sl;x;gf;gf;cpgDrive;0;.001;0];
desiredPeriod = 2;
fPeriod = @(x) desiredPeriod - tune.objective_function(xTunePeriod(x),2);
tauf = fzero(fPeriod,500);

%% Plot a phase response curve
stimDur = .1*desiredPeriod;
stimMag = 20e-9;
xPRC = @(x) [sl;-sl;tauf;sl;-sl;tauf;gf;gf;cpgDrive;x;x+stimDur;stimMag];
fPeaks = @(x) tune.objective_function(xPRC(x),3);

baselinePeakTimes = fPeaks(0);
T = baselinePeakTimes(2)-baselinePeakTimes(1);
t0 = baselinePeakTimes(1);

nPhase = 20;
phase = (1:nPhase)/nPhase;
PRC = NaN(nPhase,1);

for i=1:nPhase
    t = fPeaks(t0+phase(i)*T);
    PRC(i) = 1-(t(2) - t(1))/T;
end

figure
plot(phase,PRC,'linewidth',2)
title(sprintf('PRC, stimulus = %1.1f nA',1e9*stimMag))
ylim([-.5,.5])
grid on




