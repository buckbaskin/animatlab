function objective = plotResponse(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = NaN(numTrials,1);

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
        
        %Transform the input/output into percent of range of motion, rather
        %than mV.
        perc = (perc - Er)/R;
        rom = (rom - Er)/R;
        cpg = (cpg - Er)/R;
        
        %These are the start times of the stimuli we added to
        %SimpleServo.aproj.
        tStimulus = [3];
        
        %This is how long each stimulus is.
        stimDuration = 2;
        
        numStim = length(tStimulus);
        
        h = figure;
        
        for j=1:numStim
            [~,indStart] = min( abs( time - tStimulus(j) ) );
            [~,indEnd] = min( abs( time - (tStimulus(j)+stimDuration) ) );
            
            thisTime = time(indStart:indEnd);
            thisPerc = perc(indStart:indEnd);
            thisROM = rom(indStart:indEnd);
            thisCPG = cpg(indStart:indEnd);
            
            figure(h)
            hold on
            subplot(1,2,1)
            hold on
            % plot(thisTime - thisTime(1),thisPerc,'linewidth',2,'color',h.CurrentAxes.ColorOrder(j,:))
            hold off
            
            subplot(1,2,2)
            hold on
            plot(thisTime,thisPerc,'linewidth',2,'color',h.CurrentAxes.ColorOrder(j,:));
            plot(thisTime,thisROM,'--','color',h.CurrentAxes.ColorOrder(j,:))
            hold off
        end
        
        figure(h)
        subplot(1,2,1)
        hold on
        title(sprintf('Trial %i',i))
        xlim([0,stimDuration])
        ylabel('Norm. to comm. rotation')
        xlabel('Time (s)')
        grid on
        hold off
        
        subplot(1,2,2)
        hold on
        ylabel('Norm. to range of motion')
        xlabel('Time (s)')
        grid on
        hold off
        
        objective(i) = h;
    end
end