function peakTimes = cpgPeaks(simDataCell, colHeaders, desiredData)

    numTrials = length(simDataCell);
    peakTimes = NaN(numTrials,1);
    toPlot = true;
    smoothWindow = 25;

    for i=1:numTrials
        
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        time = data(:,timeCol);
        
        cpgCol = strcmp(colHeaders{i},'Ext HC');
        cpg = smooth(data(:,cpgCol),smoothWindow);
        
        inputCol = strcmp(colHeaders{i},'Input');
        input = data(:,inputCol);

        [~,locs] = findpeaks(cpg,time,'MinPeakHeight',-39e-3,'MinPeakDistance',.2);
        
        peakTimes = locs(1:3);
                
        if toPlot
            figure
            plot(time,cpg)
            hold on
            plot(time,input)
        end
    end    
end
