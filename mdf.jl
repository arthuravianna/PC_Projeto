using JSON


function readJSON(_filename::String)
    data = Dict()
    data = JSON.parsefile(_filename)
    return data
end

function main(_filename::String)
    println("MDF")
    data = readJSON(_filename)

    connect = data["connect"]
    cc = data["cc"]

    #=
    connect = [
        2   0   0   5;
        3   1   0   6;
        4   2   0   7;
        0   3   0   8;
        6   0   1   9;
        7   5   2   10;
        8   6   3   11;
        0   7   4   12;
        10  0   5   13;
        11  9   6   14;
        12  10  7   15;
        0   11  8   16;
        14  0   9   0;
        15  13  10  0;
        16  14  11  0;
        0   15  12  0
    ]

    cc1 = [
        1   100;
        1   75;
        1   75;
        1   0;
        1   100;
        0   0;
        0   0;
        1   0;
        1   100;
        0   0;
        0   0;
        1   0;
        1   100;
        1   25;
        1   25;
        1   0
    ]
=#    
    bloco = [4 -1 -1 -1 -1]

    n = length(connect)

    # assembly
    variables = Dict{Int, Any}()
    for i=1:n
        if cc[i][1] == 0
            variables[i] = length(variables) + 1
        end
    end

    n = length(variables)
    A = zeros(Float64, n, n)
    b = zeros(Float64, n)

    for pair in variables
        old_i = pair[1]
        new_i = pair[2]
        A[new_i,new_i] = bloco[1] #N0

        for x=1:4
            conn = connect[old_i][x]
            if conn != 0 # existe conexao
                if cc[conn][1] == 1 # ponto com valor conhecido
                    b[new_i] -= bloco[x+1] * cc[conn][2]
                else
                    A[new_i,variables[conn]] = bloco[x+1]
                end
            end
        end
    end

    x = A\b

    for pair in variables
        variables[pair[1]] = x[pair[2]] # resultado
    end

    fout = open(string("result_", _filename), "w")
    JSON.print(fout, sort(collect(variables)), 2)
    close(fout)
end

if length(ARGS) == 1
    main(ARGS[1])
end