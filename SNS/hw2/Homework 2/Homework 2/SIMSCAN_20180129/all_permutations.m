function [all_perms, m] = all_permutations( lower_limits,upper_limits,number_of_samples,linear )
%ALL_PERMUTATIONS (lower_limits, upper_limits, number_of_samples, linear)
%Returns a matrix of every possible combination of the inputs.
%   lower_limits - vector of the lower limit of each variable
%
%   upper_limits - vector of the upper limit of each variable
%
%   number_of_samples - vector of the number of samples for each variable
%
%   linear - boolean vector of whether to space the data linearly (true) or
%   logarithmically (false).
%
    if ~isequal(size(lower_limits),size(upper_limits))
        %Improper input
        error('Lower and upper limits must be the same size.')
    elseif ~isequal(size(lower_limits),size(number_of_samples))
        error('Number of samples must be the same size as the limits.')
    else
        %How many variables are there?
        n = length(lower_limits);
        
        %Initialize a cell to hold the values to sample for each variable
        all_vectors = cell(n,1);
        
        %For each dimension, make a vector holding all values to sample
        for i=1:n
            if linear(i)
                all_vectors{i} = linspace(lower_limits(i),...
                    upper_limits(i),number_of_samples(i))';
            else
                all_vectors{i} = logspace(log10(lower_limits(i)),...
                    log10(upper_limits(i)),number_of_samples(i))';
            end
        end
        
        %How many combinations are there?
        m = prod(number_of_samples);
        
        %Initialze a variable to hold all of the ndgrids.
        grids = cell(1,n);
        
        %Write the ndgrid to the variable grids
        [grids{:}] = ndgrid(all_vectors{:});
        
        %Initialize a matrix to hold our final all_perms output
        all_perms = NaN(m,n);
        
        %For each variable, lay out the variables linearly. We are
        %effectively slicing along a different variable each time because
        %of ndgrid's output.
        for i=1:n
            all_perms(:,i) = grids{i}(:);
        end
    end
end

