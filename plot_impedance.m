function plot_impedance(varargin)
% plot_impedance  plot data from an impedance data file
%   plot_impedance opens a file picker allowing one or more data
%   files to be selected, and generates an impedance plot for 
%   each data file.
%
%   plot_impedance(true) saves each plot as a JPEG.

printFigure = false;
if nargin == 1
    printFigure = varargin{1};
end

[filenames, path] = uigetfile('*.mat', 'MultiSelect', 'on');
if ischar(filenames)
    filenames = {filenames};
end

for i = 1:length(filenames)
    d(i) = read_e4990a_data(fullfile(path, filenames{i}));
    figure;
    [ha, hl1, hl2] = plotyy(d(i).Frequency, d(i).R, d(i).Frequency, d(i).X);
    [rp, ri] = max(d(i).R);
    rf = d(i).Frequency(ri);
%     line(ha(1), rf, rp, 'Marker', '^', 'MarkerSize', 8, 'MarkerFaceColor', get(hl1, 'Color'));
    if 1e3 < rp && rp < 5e3
        text(rf + 125e3, rp, sprintf('%.3f MHz, %.0f \\Omega', rf/1e6, rp), ...
            'Interpreter', 'tex', 'FontSize', 14);
    end
    hl1.LineWidth = 3;
    hl2.LineWidth = 3;
%     ylim(ha(1))
%     ylim(ha(2))
    ylim(ha(1), [0 3e3]);
    set(ha(1), 'ytick', 0:500:3e3);
    ylim(ha(2), [-40e3, 0]);
    set(ha(2), 'ytick', -40e3:10e3:0);
    [~, fname] = fileparts(filenames{i});
    title(ha(1), sprintf('Filename %s, Bias = %0.1f', fname, d(i).biasVoltage));
    if printFigure
        print('-djpeg100', fullfile(path, fname))
    end
    ylabel(ha(1), 'R (\Omega)', 'Interpreter', 'tex', 'FontSize', 14)
    ylabel(ha(2), 'X (\Omega)', 'Interpreter', 'tex', 'FontSize', 14)
end
