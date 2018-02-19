function objective = plotResponse(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = NaN(numTrials,1);
    
    for i=1:numTrials
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        commCol = strcmp(colHeaders{i},'Comm. Position');
        percCol = strcmp(colHeaders{i},'Perc. Position');
        
        time = data(:,timeCol);
        comm = data(:,commCol);
        perc = data(:,percCol);
        
        %Transform the input/output into percent of range of motion, rather
        %than mV.
        comm = (comm - -60e-3)/20e-3;
        perc = (perc - -60e-3)/20e-3;
        
        %These are the start times of the stimuli we added to
        %SimpleServo.aproj.
        tStimulus = [2,4,6,8];
        
        %This is how long each stimulus is.
        stimDuration = 2;
        
        numStim = length(tStimulus);
        
        h = figure;
        
        for j=1:numStim
            [~,indStart] = min( abs( time - tStimulus(j) ) );
            [~,indEnd] = min( abs( time - (tStimulus(j)+stimDuration) ) );
            
            thisTime = time(indStart:indEnd);
            thisComm = comm(indStart:indEnd);
            thisPerc = perc(indStart:indEnd);
            
            %Find the signed range of the commanded angle.
            rComm = comm(indEnd) - comm(indStart);
            
            %Normalize the response such that each trial starts at -1, with
            %the commanded position of 0.
            normResponse = (thisPerc - thisComm)/rComm;
            
            figure(h)
            hold on
            subplot(1,2,1)
            hold on
            plot(thisTime - thisTime(1),normResponse,'linewidth',2,'color',h.CurrentAxes.ColorOrder(j,:))
            hold off
            
            subplot(1,2,2)
            hold on
            plot(thisTime,thisPerc,'linewidth',2,'color',h.CurrentAxes.ColorOrder(j,:));
            plot(thisTime,thisComm,'--','color',h.CurrentAxes.ColorOrder(j,:))
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