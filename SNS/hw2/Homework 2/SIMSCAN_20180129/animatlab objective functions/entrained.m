function objective = entrained(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    objective = cell(2,numTrials);
    
    for i=1:numTrials
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        flxVelCol = strcmp(colHeaders{i},'Flx Vel Inter');
        posCol = strcmp(colHeaders{i},'Joint_1 Perceived Position');
        pepCol  = strcmp(colHeaders{i},'LM_FTi PEP Sum');
        
        time = data(:,timeCol);
        flxVel = data(:,flxVelCol);
        pos = data(:,posCol);
        pep = data(:,pepCol);
        
%         figure
%         plot(flxVel)
%         hold on
%         plot(pos)
%         plot(pep)
%         legend('flx','pos','pep')
%         hold off
%         drawnow
        
        instEntrained = (flxVel > (-60 + 2.9 )*1e-3) & (pos < pep);
        isEntrained = any(instEntrained);
        objective{1,i} = double(isEntrained);
        objective{2,i} = max(flxVel(time > 1));
    end
end