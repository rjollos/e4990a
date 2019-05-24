function d = read_e4990a_data(filename)
% read_e4990a_data  read data acquired from the Keysight E4990A
%   d = read_e4990a_data(filename) reads the mat file FILENAME and
%   returns a data structure with the numeric values of type DOUBLE.

d = load(filename);

fn = fieldnames(d);
for i = 1:length(fn)
    if isa(d.(fn{i}), 'integer') || isa(d.(fn{i}), 'single')
        d.(fn{i}) = double(d.(fn{i}));
    end
end