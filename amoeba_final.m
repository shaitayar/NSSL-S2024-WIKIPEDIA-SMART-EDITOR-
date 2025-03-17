%%
clear;
clc;
close all
%%
csvFilePath = 'exports\\amoeba\\users_to_amoeba'; 
users = readtable(csvFilePath);
numRuns = 20;

outputFile = 'exports\\amoeba\\optimization_results.csv';
if exist(outputFile, 'file')
    delete(outputFile);
end
fid = fopen(outputFile, 'w');
fprintf(fid, 'x1,x2,x3,objective\n');
fclose(fid);

%%
for i = 1:numRuns
    initialGrades = rand(1, 3);

    options = optimset('OutputFcn', @(x, optimValues, state) logPoints(x, optimValues, state, outputFile), 'Display', 'iter');

    objective = @(grades) -computeMeanProPalestine(grades, users);
    
    global iterationHistory;
    iterationHistory = struct('iteration', [], 'fval', []);

    %fminsearch with the options
    [optimizedGrades, negMeanProPalestine] = fminsearch(objective, initialGrades, options);
    
    % display
    disp('Optimized Grades:');
    disp(optimizedGrades);
    
    disp('Mean of pro-Palestine in pruned list:');
    disp(-negMeanProPalestine);  
    
    iterations = [iterationHistory.iteration];
    fvals = [iterationHistory.fval];
    
    % plot 
    figure;
    plot(iterations, -fvals, '-o');
    xlabel('Iteration');
    ylabel('Objective Function Value');
    title(sprintf('Optimization [%0.3f, %0.3f, %0.3f] → [%0.3f, %0.3f, %0.3f]', ...
        initialGrades(1), initialGrades(2), initialGrades(3), ...
        optimizedGrades(1), optimizedGrades(2), optimizedGrades(3)));
    
    grid on;
end
%% Function Definitions
function stop = logPoints(x, optimValues, state, outputFile)
    stop = false;
    global iterationHistory;
    
    if strcmp(state, 'init')
        iterationHistory.iteration = [];
        iterationHistory.fval = [];
    elseif strcmp(state, 'iter')

        fid = fopen(outputFile, 'a');
        fprintf(fid, '%f,%f,%f,%f\n', x(1), x(2), x(3), optimValues.fval);
        fclose(fid);
        
        iterationHistory.iteration = [iterationHistory.iteration; optimValues.iteration];
        iterationHistory.fval = [iterationHistory.fval; optimValues.fval];
    end
end

function meanProPalestine = computeMeanProPalestine(grades, users)
    prunedUsers = pruneList(grades, users);

    proPalestineUsers = prunedUsers(prunedUsers.pro_palestine == 1, :);

    if ~isempty(prunedUsers)
        meanProPalestine = height(proPalestineUsers) / height(prunedUsers);
    else
        meanProPalestine = 0; 
    end
end

function prunedUsers = pruneList(grades, users)
    prunedUsers = users(1,:); 
    prunedUsers(1,:) = []; 

    for i = 1:height(users)
        if meetsGradeCondition(grades, users(i,:))
            prunedUsers = [prunedUsers; users(i,:)]; 
        end
    end
end

function result = meetsGradeCondition(grades, userRow)
    if (isnan(userRow{1,'total_contribs'}) || userRow{1,'protected_contribs'}==0)
        g1 = 0;
    else 
        g1 = (userRow{1,'protected_contribs'} / userRow{1,'total_contribs'}) * grades(1);
    end

    if(ismissing(userRow{1, 'registration'}) || ismissing(userRow{1, 'ec_timestamp'}))
        g2 = 0;
    else
        registrationDate = datetime(userRow{1, 'registration'}, 'InputFormat', 'yyyy-MM-dd''T''HH:mm:ss''Z''');
        ecTimestamp = datetime(userRow{1, 'ec_timestamp'}, 'InputFormat', 'yyyy-MM-dd''T''HH:mm:ss''Z''');
        monthsUntilEc = calculateMonthsDifference(registrationDate, ecTimestamp);

        g2 = (1 / (1 + monthsUntilEc)) * grades(2);
    end 

    
    if (isnan(userRow{1,'total_reverts'}) || userRow{1,'protected_reverts'}==0)
        g3 = 0;
    else    
        g3 = ((userRow{1,'protected_reverts'})/(userRow{1,'total_reverts'})) * grades(3);
    end 
    %sum
    result = (g1 + g2 + g3) >= 0.5;
    %fprintf('%f %f %f',g1, g2,g3);
end

function monthsDiff = calculateMonthsDifference(date1, date2)
    monthsDiff = calmonths(between(date1, date2, 'months'));
end
