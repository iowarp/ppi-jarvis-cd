#!/bin/bash
# Bash completion for Jarvis CD
# Source this file or place it in /etc/bash_completion.d/ or /usr/share/bash-completion/completions/

_jarvis_completion() {
    local cur prev words cword split
    _init_completion -s || return

    # Find the jarvis-completion-helper script
    local helper_script
    if [[ -x "$(dirname "$(which jarvis 2>/dev/null)")/jarvis-completion-helper" ]]; then
        helper_script="$(dirname "$(which jarvis)")/jarvis-completion-helper"
    elif [[ -x "./bin/jarvis-completion-helper" ]]; then
        helper_script="./bin/jarvis-completion-helper"
    else
        # Fallback - no completion available
        return 0
    fi

    # Get the current command path
    local cmd_path=("${words[@]:1:$((cword-1))}")
    local current_word="${words[cword]}"
    local previous_word="${words[cword-1]}"

    # Handle different completion contexts
    case "${#cmd_path[@]}" in
        0)
            # Completing main commands
            local commands=$($helper_script commands 2>/dev/null)
            COMPREPLY=($(compgen -W "$commands" -- "$current_word"))
            ;;
        1)
            # Completing subcommands
            local main_cmd="${cmd_path[0]}"
            case "$main_cmd" in
                config|bootstrap|resource-graph|repo|env|pipeline|pkg|ssh|sched)
                    local subcommands=$($helper_script subcommands "$main_cmd" 2>/dev/null)
                    COMPREPLY=($(compgen -W "$subcommands" -- "$current_word"))
                    ;;
                *)
                    # No subcommands for this command
                    return 0
                    ;;
            esac
            ;;
        2)
            # Completing arguments for subcommands
            local main_cmd="${cmd_path[0]}"
            local sub_cmd="${cmd_path[1]}"
            
            case "$main_cmd $sub_cmd" in
                "pipeline append"|"pipeline prepend")
                    # Complete with package names
                    local packages=$($helper_script packages 2>/dev/null)
                    COMPREPLY=($(compgen -W "$packages" -- "$current_word"))
                    ;;
                "pipeline insert")
                    # First arg should be a pipeline ID, second should be package name
                    if [[ $cword -eq 4 ]]; then
                        local packages=$($helper_script packages 2>/dev/null)
                        COMPREPLY=($(compgen -W "$packages" -- "$current_word"))
                    fi
                    ;;
                "pkg help"|"pkg readme"|"pkg src"|"pkg root")
                    # Complete with package names
                    local packages=$($helper_script packages 2>/dev/null)
                    COMPREPLY=($(compgen -W "$packages" -- "$current_word"))
                    ;;
                "pipeline "*|"pkg configure"|"pkg unlink"|"pkg remove")
                    # Complete with pipeline names
                    local pipelines=$($helper_script pipelines 2>/dev/null)
                    COMPREPLY=($(compgen -W "$pipelines" -- "$current_word"))
                    ;;
                "resource-graph add")
                    COMPREPLY=($(compgen -W "storage net" -- "$current_word"))
                    ;;
                "resource-graph filter")
                    COMPREPLY=($(compgen -W "fs net" -- "$current_word"))
                    ;;
                "pipeline env")
                    COMPREPLY=($(compgen -W "build scan track path show copy" -- "$current_word"))
                    ;;
                "pipeline index")
                    COMPREPLY=($(compgen -W "show copy load" -- "$current_word"))
                    ;;
                "pipeline load")
                    COMPREPLY=($(compgen -W "yaml" -- "$current_word"))
                    ;;
                "pipeline run")
                    COMPREPLY=($(compgen -W "yaml" -- "$current_word"))
                    ;;
                "pipeline update")
                    COMPREPLY=($(compgen -W "yaml" -- "$current_word"))
                    ;;
                "repo create")
                    # First arg is package type name, second is package class
                    if [[ $cword -eq 4 ]]; then
                        COMPREPLY=($(compgen -W "service app interceptor" -- "$current_word"))
                    fi
                    ;;
                "sched hostfile")
                    COMPREPLY=($(compgen -W "build" -- "$current_word"))
                    ;;
                *)
                    # For file/directory arguments, use default completion
                    if [[ "$current_word" == /* || "$current_word" == ./* || "$current_word" == ../* ]]; then
                        _filedir
                    fi
                    ;;
            esac
            ;;
        3)
            # Handle three-level commands
            local main_cmd="${cmd_path[0]}"
            local sub_cmd="${cmd_path[1]}"
            local subsub_cmd="${cmd_path[2]}"
            
            case "$main_cmd $sub_cmd $subsub_cmd" in
                "pipeline load yaml"|"pipeline run yaml"|"pipeline update yaml")
                    # Complete with YAML files
                    _filedir '@(yml|yaml)'
                    ;;
                "resource-graph add storage"|"resource-graph add net"|"resource-graph filter fs"|"resource-graph filter net")
                    # These typically need file arguments or specific parameters
                    _filedir
                    ;;
                "pipeline insert "*)
                    # For pipeline insert, after the position and package type, we might have package ID
                    if [[ $cword -eq 5 ]]; then
                        # This would be the package ID - could suggest the same as package type
                        local packages=$($helper_script packages 2>/dev/null)
                        COMPREPLY=($(compgen -W "$packages" -- "$current_word"))
                    fi
                    ;;
                *)
                    # Default file completion for other cases
                    if [[ "$current_word" == /* || "$current_word" == ./* || "$current_word" == ../* ]]; then
                        _filedir
                    fi
                    ;;
            esac
            ;;
        *)
            # For deeper nesting or when we have many arguments, try some intelligent defaults
            case "$previous_word" in
                --*=*)
                    # Handle --option=value format
                    return 0
                    ;;
                --partition)
                    # Common SLURM partitions
                    COMPREPLY=($(compgen -W "compute debug gpu" -- "$current_word"))
                    ;;
                --time|--walltime)
                    # Time format examples
                    COMPREPLY=($(compgen -W "00:10:00 01:00:00 12:00:00 24:00:00" -- "$current_word"))
                    ;;
                --output-file|--error-file)
                    _filedir
                    ;;
                *)
                    # Default to file completion if it looks like a path
                    if [[ "$current_word" == /* || "$current_word" == ./* || "$current_word" == ../* ]]; then
                        _filedir
                    fi
                    ;;
            esac
            ;;
    esac

    # Handle special cases for flag arguments
    if [[ "$current_word" == -* ]]; then
        # Common flags across commands
        local common_flags="--help -h --conf --no-conf --force --resume"
        COMPREPLY=($(compgen -W "$common_flags" -- "$current_word"))
    fi
}

# Register the completion function
complete -F _jarvis_completion jarvis