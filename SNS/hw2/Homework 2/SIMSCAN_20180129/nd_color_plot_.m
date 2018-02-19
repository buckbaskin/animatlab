function [ fig_handle, is_linear ] = nd_color_plot_( x_data, z_data )
%ND_COLOR_PLOT Plots an arbitrarily high dimensional plot by plotting
%surfaces for each data point
%   nd_color_plot( x_data, z_data, plot_as_contour )
    [m,n] = size(x_data);
    
%     if any(isnan(z_data))
%         error('Some Z data is NaN.')
%     end
    
    if (m == 1 && n ~= 1)
        x_data = x_data';
        z_data = z_data';
        m_temp = m;
        m = n;
        n = m_temp;
    end
    
    if size(z_data,1) ~= m
        error('The X and Z data must have the same number of rows.')
    end
    
    if n == 1 || m == 1
        %2D scatter
        figure
        clf
        hold on
        grid on
        plot(x_data,z_data,'Linewidth',2)
        hold off
    else
        %even number of columns
        
        %define metrics about each data column that will be needed later.
        unique_vals = cell(n,1);
        num_unique_vals = NaN(n,1);
        dx = NaN(n,1);
        min_vals = NaN(n,1);
        range_vals = NaN(n,1);
        is_linear = ones(n,1);
        
        for i=1:n
            %Pick out the unique values for each variable, and find the
            %number of them, the minimum value, and the range of each
            %column.
            u_vals = unique(x_data(:,i));
            unique_vals{i} = u_vals;
            num_unique_vals(i) = length(u_vals);
            
            
            if all(abs(diff(diff(u_vals))) < 1e-12)
                dx(i) = mean(diff(u_vals));
                min_vals(i) = min(u_vals);
                range_vals(i) = range(u_vals); 
            else
                if all(u_vals > 0) && all(abs(diff(diff(log10(u_vals))))) < 1e-12
                    is_linear(i) = 0;
                    x_data(:,i) = log10(x_data(:,i));
                    dx(i) = mean(diff(log10(u_vals)));
                    min_vals(i) = min(log10(u_vals));
                    range_vals(i) = range(log10(u_vals)); 
                else
                    error('Data must be linearly or logarithmically spaced.')
                end
            end
            
        end
        %We are going to plot our n-dimensional data as a 2D set, so we
        %will map the extra dimensions to the primary two dimensions.
        %Initialize the new x matrix.
        new_x = NaN(m,2);
        
        %Split the data into columns plotted along the horizontal axis, and
        %those along the vertical axis. For convenience of notation, split
        %up all metrics this way.
        horiz_inds = 1:ceil(n/2);
        horiz_x = x_data(:,horiz_inds);
        horiz_dx = dx(horiz_inds);
        new_x(:,1) = horiz_x(:,1);
        horiz_min = min_vals(horiz_inds);
        horiz_range = range_vals(horiz_inds);
        horiz_unique = num_unique_vals(horiz_inds);
        
        vert_inds = ceil(n/2)+1:n;
        vert_x = x_data(:,vert_inds);
        vert_dx = dx(vert_inds);
        new_x(:,2) = vert_x(:,1);
        vert_min = min_vals(vert_inds);
        vert_range = range_vals(vert_inds);
        vert_unique = num_unique_vals(vert_inds);
        
        for i=1:m
            for j=2:ceil(n/2)
                new_x(i,1) = new_x(i,1) + horiz_dx(1)*prod(1./horiz_unique(2:j-1))*...
                    (horiz_x(i,j)-horiz_min(j))/(horiz_range(j)+horiz_dx(j));
            end
        end
        
        for i=1:m
            for j=2:floor(n/2)
                new_x(i,2) = new_x(i,2) + vert_dx(1)*prod(1./vert_unique(2:j-1))*...
                    (vert_x(i,j)-vert_min(j))/(vert_range(j)+vert_dx(j));
            end
        end
        
        %To properly plot the surface, sort the indices. First by the
        %second column, then by the first. The first column will then have
        %the largest segments with adjacent values.
        [~,inds] = sort(new_x(:,2));
        new_x(:,1) = new_x(inds,1);
        new_x(:,2) = new_x(inds,2);
        z_data = z_data(inds);
        
        [~,inds] = sort(new_x(:,1));
        new_x(:,1) = new_x(inds,1);
        new_x(:,2) = new_x(inds,2);
        z_data = z_data(inds);
        
        %To plot a surface, we'll need the data in a grid. Find the size of
        %the grid.
        y_length = prod(num_unique_vals(1:ceil(n/2)));
        x_length = m/y_length;
        
        %Turn new_x into a grid
        X = reshape(new_x(:,1),x_length,y_length);
        Y = reshape(new_x(:,2),x_length,y_length);
        Z = reshape(z_data,size(X));
        z_min = min(z_data);
        z_max = max(z_data);
            
        v = linspace(z_min,z_max,10);

        %Plot the figure
        fig_handle = figure;            
        clf
        hold on
%         scatter3(new_x(:,1),new_x(:,2),z_data,5000,z_data,'.')
        scatter3(new_x(:,1),new_x(:,2),z_data,500,z_data,'.')
        view(0,90)
        xlabel('x_1')
        ylabel(['x_',num2str(ceil(n/2)+1)])

        %Plot grid lines that demark the variables.
        ph = zeros(2,1); %place holder
        x_min = min(min(X));
        x_max = max(max(X));
        y_min = min(min(Y));
        y_max = max(max(Y));

        
        xlim([x_min,x_max]);
        ylim([y_min,y_max]);
        
        total_range = range(new_x(:,1)) + horiz_dx(1)/prod(horiz_unique(2:ceil(n/2)));
        for i=1:ceil(n/2)
            %find the number of lines to draw, and the range over which they
            %must be drawn.
            j = ceil(n/2)+1-i;
            
            num_lines = prod(horiz_unique(1:j));
            
            k = 1;
            %Plot each line with two points, at the maximum z value, so it
            %is visible above the surface. Change the line thickness each
            %time.
            while k < num_lines
                x_val = x_min + k*total_range/num_lines;
                plot3(x_val+ph,[y_min,y_max],z_min+ph,'black','Linewidth',i);
                k = k + 1;
            end
        end
        
        total_range = range(new_x(:,2)) + vert_dx(1)/prod(vert_unique(2:floor(n/2)));
        for i=1:floor(n/2)
            j = floor(n/2)+1-i;
            
            num_lines = prod(vert_unique(1:j));
            
            k = 1;
            while k < num_lines
                y_val = y_min + k*total_range/num_lines;
                plot3([x_min,x_max],y_val+ph,z_min+ph,'black','Linewidth',i);
                k = k + 1;
            end
        end
        
        colorbar
        hold off        
    end
end

