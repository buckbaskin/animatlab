% - Is proportional control stable?
% - Can you, given the matrix of a system or its computed eigen values and
% eigen vectors, perturb the values of the system to try and find the
% nearest small change that makes the system stable?
% - Can you quantify how stable? By my checks below, the system is as stable
% as its smallest, eigen value.
% 


% Build up a matrix with negative eigen values
% write out column vectors, then transpose
P = [[1 2 0];
     [3 4 0];
     [0 0 1]]';
% write out eigen values as a vector, then diagonalize
D = diag([-2 -1+1i -0.5]);
% rebuild the system
rebuild = P*D/P;

K_p = 1;
K_v = 0.1;

% System will be defined by linear system analysis
system = [[0 1]; [-K_p -K_v]];
disp('System:');
disp(system);
[eigen_vectors, eigen_valuesD] = eig(system);
eigen_valuesC = diag(eigen_valuesD);

revC = real(eigen_valuesC);
ievC = imag(eigen_valuesC);

stable = all(revC < 0);
divergent = any(revC > 0);
oscillatory = any(ievC ~= 0);

disp('Analysis');
if stable
    if oscillatory
        disp('Stable but oscillatory');
    else
        disp('System is stable');
    end
elseif divergent
    disp('System will diverge');
else
    disp('System is not stable');
end
fprintf('\nEigen Values:\n');
disp(eigen_valuesC);