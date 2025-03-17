%%
clear all;
clc;
%%
data = readtable('exports\\amoeba\\optimization_results.csv'); 

x1 = data.x1;
x2 = data.x2;
x3 = data.x3;
objective = -data.objective;

[x1Grid, x2Grid] = meshgrid(linspace(min(x1), max(x1), 50), linspace(min(x2), max(x2), 50));

objectiveGrid = griddata(x1, x2, objective, x1Grid, x2Grid, 'linear');

figure;
surf(x1Grid, x2Grid, objectiveGrid); 
colorbar; 
xlabel('Grade 1 (Contributions to EC Pages)');
ylabel('Grade 2 (EC Tag)');
zlabel('MeanProPalestine');
title('Optimization Surface: Contributions to EC & EC Tag');
grid on;
shading interp; 


%x1, x3
[x1Grid, x3Grid] = meshgrid(linspace(min(x1), max(x1), 50), linspace(min(x3), max(x3), 50));
objectiveGrid = griddata(x1, x3, objective, x1Grid, x3Grid, 'linear');
figure;
surf(x1Grid, x3Grid, objectiveGrid);
colorbar;
xlabel('Grade 1 (Contributions to EC Pages)');
ylabel('Grade 3 (Reverts in EC Pages)');
zlabel('MeanProPalestine');
title('Optimization Surface: Contributions to EC vs Reverts in EC');
grid on;
shading interp;

%x2, x3
[x2Grid, x3Grid] = meshgrid(linspace(min(x2), max(x2), 50), linspace(min(x3), max(x3), 50));
objectiveGrid = griddata(x2, x3, objective, x2Grid, x3Grid, 'linear');
figure;
surf(x2Grid, x3Grid, objectiveGrid);
colorbar;
xlabel('Grade 2 (EC Tag)');
ylabel('Grade 3 (Reverts in EC Pages)');
zlabel('MeanProPalestine');
title('Optimization Surface: EC Tag vs Reverts in EC Pages');
grid on;
shading interp;
