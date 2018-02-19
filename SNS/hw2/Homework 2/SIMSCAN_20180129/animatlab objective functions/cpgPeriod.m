function period = cpgPeriod(simDataCell, colHeaders, desiredData)

    numTrials = length(simDataCell);
    period = NaN(numTrials,1);
    toPlot = false;
    
    if toPlot
        figure
        hold on
        legendCell = cell(numTrials,1);
    end

    for i=1:numTrials

        smoothWindow = 25;
        
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        time = data(:,timeCol);
        
        cpgCol = strcmp(colHeaders{i},'Ext HC');
        cpg = data(:,cpgCol);
        
        m = size(time,1);
        beginSS = floor(0.1*m);

        dt = mean(diff(time));

        cpg = smooth(cpg(beginSS:m),smoothWindow);

        period(i) = find_period(cpg,0.25,1,dt);
        
        if toPlot
            plot(time(beginSS:m),cpg)
            legendCell{i} = ['Trial ',num2str(i)];
        end
    end
    
    if toPlot
        legend(legendCell)
    end
    
end
