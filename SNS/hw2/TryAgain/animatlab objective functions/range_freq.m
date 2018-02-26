function objective = range(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = NaN(numTrials,2);

    Er = -60e-3;
    R = 20e-3;
    
    for i=1:numTrials
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        percCol = strcmp(colHeaders{i},'Perc. Position');
        romCol = strcmp(colHeaders{i},'Range of Motion 2');
        cpgCol = strcmp(colHeaders{i},'CPG Speed 2');
        
        time = data(:,timeCol);
        perc = data(:,percCol);
        rom = data(:,romCol);
        cpg = data(:,cpgCol);
        
        %Transform the input/output into percent of stimulation instead of
        %mV
        perc = (perc - Er)/R;
        rom = (rom - Er)/R;
        cpg = (cpg - Er)/R;
        
        %These are the start times of the stimuli we added to
        %SimpleServo.aproj.
        tStimulus = [3];
        
        %This is how long each stimulus is.
        stimDuration = 2;
        
        numStim = length(tStimulus);
        
        % h = figure;
        
        for j=1:numStim
            [~,indStart] = min( abs( time - tStimulus(j) ) );
            [~,indEnd] = min( abs( time - (tStimulus(j)+stimDuration) ) );
            
            thisTime = time(indStart:indEnd);
            thisPerc = perc(indStart:indEnd);
            thisROM = rom(indStart:indEnd);
            thisCPG = cpg(indStart:indEnd);
            
            maxPerc = max(max(thisPerc));
            minPerc = min(min(thisPerc));
            avgROM = mean2(thisROM);
            avgCPG = mean2(thisCPG);
            measured_ROM = maxPerc - minPerc;
            objective(i,1) = avgROM;
            objective(i,2) = measured_ROM;
        end
    end
end
