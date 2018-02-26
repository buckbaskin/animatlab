function objective = range(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = NaN(numTrials,4);

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
            
            [maxPerc, maxIndex] = max(thisPerc);
            max_time = thisTime(maxIndex);
            [minPerc, minIndex] = min(thisPerc);
            min_time = thisTime(minIndex);
            avgROM = mean2(thisROM);
            avgCPG = mean2(thisCPG);
            
            measured_ROM = maxPerc - minPerc;
            rise_time = abs(max_time - min_time);
            cpgFreq = 1.0 / rise_time;
            
            objective(i, 1) = avgROM;
            objective(i, 2) = measured_ROM;
            objective(i, 3) = avgCPG;
            objective(i, 4) = cpgFreq;
        end
    end
end
