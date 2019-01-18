function d = read_e4990a_data(filename)

d = load(filename);

fn = fieldnames(d);
for i = 1:length(fn)
    if isa(d.(fn{i}), 'integer') || isa(d.(fn{i}), 'single')
        d.(fn{i}) = double(d.(fn{i}));
    end
end