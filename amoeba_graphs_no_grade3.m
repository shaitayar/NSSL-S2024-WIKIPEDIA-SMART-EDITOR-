
clear all;
clc;
%%
data = readtable('exports\\amoeba\\optimization_results_no_grade_3.csv'); 

x1 = data.x1;
x2 = data.x2;
objective = -data.objective;

[x1Grid, x2Grid] = meshgrid(linspace(min(x1), max(x1), 50), linspace(min(x2), max(x2), 50));

objectiveGrid = griddata(x1, x2, objective, x1Grid, x2Grid, 'linear');

figure;
surf(x1Grid, x2Grid, objectiveGrid); % "blanket" 
colorbar; 
xlabel('Grade 1 (Contributions to EC Pages)');
ylabel('Grade 2 (EC Tag)');
zlabel('MeanProPalestine');
title('Optimization Surface: Contributions to EC & EC Tag');
grid on;
shading interp; % smooth surface


