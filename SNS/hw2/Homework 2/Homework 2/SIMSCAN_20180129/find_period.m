function [ mean_period, std_period, num_periods ] = find_period( V, expected_minimum_period, min_num_peaks, dt )
%FINDPERIOD Calculates the fundamental period of an oscillating dataset by
%clipping the signal at various heights and averaging the time to between
%threshold crossings. Returns [T_mean, T_std, T_num].
    %Look for spikes and find the period of oscillation    
    diagnostic = false;
    
    %First, make sure the input is the proper size: a column vector
    [rows,cols] = size(V);
    
    if rows > 1 && cols > 1
        disp('find_period input is not the correct size.')
    elseif rows > 1 && cols == 1
        %proper form
    elseif rows == 1 && cols > 1
        V = V';
    elseif rows == 1 && cols == 1
        disp('find_period input must be a vector.')
    else
        disp('find_period input must not be empty.')
    end
    
    %Smooth V
%     blocks = 20;
%     block_filt = ones(1,blocks)/blocks;
%     V = filtfilt(block_filt,1,V)
    
    
    %Compute the "normalized" data, that is, with the maximum peak at f=1,
    %then compute the autocorrelation of the signal.
%     percent_to_clip = 0.2;
%     inds = round(percent_to_clip*length(V));
%     f = V(inds:end)-mean(V);
    %The data should be clipped to remove transients before calling
    %find_period.
    f = V-mean(V);
    max_f = max(f);
    if max_f == 0
        %f = f;
    else
        f = f/max_f;
    end
    autocor = xcorr(f,round(length(V)/2));
    
    %Find the maxima of the autocorrelation, which should be spaced out at
    %the period of the signal.
    [f_peaks,t_peaks] = findpeaks(autocor,'MinPeakDistance',expected_minimum_period,'MinPeakHeight',0);
    num_peaks = length(f_peaks);
    
    if num_peaks <= 1
        %There is no periodicity
        if diagnostic
            title_str = 'not oscillating';
        end
        mean_period = NaN;
        std_period = 0;
        num_periods = -1;
    elseif num_peaks <= 2*min_num_peaks+1
        if min(t_peaks) > max(diff(t_peaks))
            %We have effectively have 2 unique points, so any fit will have
            %an r_sq=1. Therefore we can see if the time of the first peak
            %happens within the maximum amount of time between peaks. For
            %instance, peaks at 1400, 1500, and 1600 suggest that there is
            %a single cycle but no sustained activity, since we would
            %expect a peak roughly every 100 in that scenario.
            %So we can say that there is no oscillation in this case.
            if diagnostic
                title_str = 'not oscillating.';
            end
            mean_period = NaN;
            std_period = 0;
            num_periods = -1;
        else
            %There is not enough data to determine periodicity
            if diagnostic
                title_str = 'more time required.';
            end
            mean_period = -1;
            std_period = 0;
            num_periods = -1;
        end
    else
        %The signal is oscillating, so continue.
        %Now that we have the peaks, we will compute the height of the highest
        %peak, as well as the time for that peak for the sake of curve fitting.
        %If we can make a linear fit with a squared residual equal to 1, then
        %our signal is not losing energy. If the squared residual is less than
        %1, then the signal is losing energy over time, and is not truly
        %oscillating.
        f_max = f_peaks(ceil(num_peaks/2));
        t_mid = t_peaks(ceil(num_peaks/2));

        %Adjust the height of the peaks such that the center peak is at 0, then
        %reflet the second half of the peaks about 0, to make a monotonically
        %increasing line.
        f_peaks = f_peaks - f_max;
        f_peaks(ceil(num_peaks/2):end) = -f_peaks(ceil(num_peaks/2):end);

        fit_func = @(t,m) m*(t-t_mid);

        %Find the slope of the line for the sake of evaluating the squared
        %residual
        p = polyfit(t_peaks,f_peaks,1);
        m = p(1);

        %Compute r_sq
        residual_sum_of_squares = 0;
        for i=1:num_peaks
            residual_sum_of_squares = residual_sum_of_squares + (f_peaks(i) - fit_func(t_peaks(i),m))^2;
        end    

        total_sum_of_squares = sum(f_peaks.^2);

        r_sq = 1-residual_sum_of_squares/total_sum_of_squares;
        if r_sq > 1
            disp(['r_sq = ',num2str(r_sq)]);
            keyboard
        end

        %Test to see if energy is decreasing. If so, then our signal is not
        %actually oscillating.
        if r_sq < 1 - 1e-2
            %The signal energy is decaying
            if diagnostic
                title_str = 'not oscillating.';
            end
            mean_period = NaN;
            std_period = r_sq;
            num_periods = -1;
        else
            if diagnostic
                title_str = 'oscillating.';
            end
            mean_period = mean(diff(t_peaks))*dt;
            std_period = std(diff(t_peaks))*dt;
            num_periods = num_peaks-1;
        end
    end
    
    if diagnostic
        h1 = figure;
        clf
        hold on
        title(['data',' ',title_str])
        plot(V)
        grid on
        h1.Position = [14,570,560,420];
        hold off

        h2 = figure;
        clf
        hold on
        title(['autocorrelation',' ',title_str])
        plot(autocor)
        grid on
        h2.Position = [580,570,560,420];
        hold off

        h3 = figure;
        clf
        hold on
        title(['data and fit',' ',title_str])
        plot(t_peaks,f_peaks,'go')
        if num_peaks > 3
            plot(t_peaks,fit_func(t_peaks,m))
        end
        grid on
        h3.Position = [1130,570,560,420];
        hold off
        
        disp('inside find_period')
        keyboard
        
        close all
    end

end

