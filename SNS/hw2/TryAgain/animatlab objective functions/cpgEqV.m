function Veq = cpgEqV(simDataCell, colHeaders, desiredData)
    numTrials = length(simDataCell);
    Veq = NaN(numTrials);
    toPlot = false;
    
    for i=1:numTrials
        data = simDataCell{i}(1:end-10,:);
        timeCol = strcmp(colHeaders{i},'Time');
        time = data(:,timeCol);
        
        cpgCol = strcmp(colHeaders{i},'Ext HC');
        Vcpg = data(:,cpgCol);
        
        dVdt = diff(Vcpg)./diff(time);
        
        Veq(i) = Vcpg(find(abs(dVdt) < sqrt(eps) & time(2:end) > 2,1,'first'));
        
        if toPlot
            figure %#ok<UNRCH>
            plot(time,Vcpg)
        end
    end
end