system = [[1, 2];[1, 2]];
[eigen_vectors, eigen_valuesD] = eig(system);
eigen_valuesC = diag(eigen_valuesD);

stable = all(eigen_valuesC < 0);
divergent = any(eigen_valuesC > 0);

if stable
    disp('System is stable');
elseif divergent
    disp('System will diverge');
else
    disp('System is not stable');
end
disp('Eigen Values:');
disp(eigen_valuesC);