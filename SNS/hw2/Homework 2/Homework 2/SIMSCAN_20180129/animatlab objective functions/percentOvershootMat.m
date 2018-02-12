function objective = percentOvershootMat(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = NaN(numTrials,1);
    
    desiredPO = 0;
    desiredRT = 0.4; %s
    
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
        po = NaN(numStim,1);
        rt = NaN(numStim,1);
        
%         h = figure;
%         g = figure;
        
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
            
%             figure(h)
%             hold on
%             plot(normResponse)
%             hold off
%             
%             figure(g)
%             hold on
%             plot(thisTime,thisPerc);
%             hold off
            
            po(j) = 100*max(normResponse);
            
            [~,tenInd] = min( abs( normResponse - -0.9 ) );
            [~,ninetyInd] = min( abs( normResponse - -0.1 ) );
            
            rt(j) = thisTime(ninetyInd) - thisTime(tenInd);
            
        end
        
        objective(i) = sum((po - desiredPO).^2) + sum((rt - desiredRT).^2);
    end
end