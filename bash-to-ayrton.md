* posix                                                                         WONTDO

* simple commands                                                               DONE

* pipelines ( a | b )                                                           DONE
  * |&
  * exit status:
    * last command                                                              CHECK
    * pipefail -> last,  right-most non-zero
    + PIPESTATUS
    * !                                                    `bool`               CHECK
  * time -> sys + user times
    * implement as `time()` function?
  * `lastpipe` can't be implemented                                             WONTDO

* lists:
  * ;,                                                                          WONTDO
  * &,                                                    `_bg=True`            DONE
    * return status is 0
  * &&,                                                   `and`                 DONE
  * ||                                                    `or`                  DONE

* Compound commands
  * (list) subshell                                                             MAYBE
    * could be implemented with `with`
  * {} (block)                                                                  DONE
  * (()) arithmetic expression                                                  CHECK
  * [[]] conditional expression w/o word split or path exp.                     WONTDO
  * ==, != right op as pattern, see patter matching                             CHECK
  * =~                                                    `re`                  DONE

  * () (precedence)                                                             DONE
  * !                                                                           DONE
  * &&                                                                          DONE
  * ||                                                                          DONE

  * for                                                                         DONE
  * for (( e1; e2; e3 )) do...                                                  WONTDO
  * select                                                                      MAYBE
  * case                                                                        WONTDO
    * use if + elif
  * if                                                                          DONE
  * while                                                                       DONE
  * until                                                                       WONTDO

* coproc                                                                        MAYBE

* function definitions                                                          DONE

* quoting                                                                       DONE
  * python flavor

* parameters
  * variables                                                                   DONE
  * no value -> null                                                            WONTDO
  * tilde, parameter, variable expansion                  use expansions        MANUAL
  * quote removal                                                               WONTDO
  * integer attribute                                     `int`                 DONE
  * "$@"                                                                        DONE
  * nameref                                               `globals()` or `locals()`
  `                                                                             DONE
  * positional                                            `args` + function params
                                                                                DONE
  * special
    * *                                                   `args[1:]` or `for arg in args`
                                                                                DONE
    * @                                                   `args`                DONE
    * #                                                   `len(args)`           DONE
    * ?                                                   `command.exit_status` DONE
    * -                                                                         WONTDO
    * $                                                   `os.getpid()`         DONE
    * !                                                                         CHECK
    * 0                                                                         CHECK
    * _                                                                         WONTDO

  * shell variables
    * IFS

  * arrays                                                `list`, `dict`        DONE
    * NOTE: python `list`s can't be sparse, use a `dict`
    * declare -a                                          `list`                DONE
    * declare -A                                          `dict`                DONE
    * assign                                                                    DONE
      * python flavor
    * ${name[subscript]}                                  `name[subscript]`     DONE
      * "${name[*]}"                                      `IFS[0].join(name)`   DONE
      * "${name[@]}"                                      `name`                DONE
    * expansion in word                                   string formatting + `name[0]
                                                                                DONE
    * ${#name[subscript]}                                 `len(name[subscript])`
                                                                                DONE
    * ${#name[@]}                                         `len(name)`           DONE
    * ${name[-x]}                                         `name[-x]`            DONE
    * ${name}                                             `name[0]`             DONE
    * create array on assign to subscript                                       WONTDO
    * ${!name[@]}                                         `range(len(name))`, `name.keys()`
                                                                                DONE
    * unset name[@]                                       `del name`            DONE
    * pathname expansion                                  use path expansion manually
                                                                                CHECK
    * read -a

* expansion (in that order)
  * brace
    * explodes words
    * pre{c,s,v}pos -> [ precpos, prespos, prevpos ]                            CHECK
    * nested                                                                    CHECK
    * {x..y[..incr]}
      * digits
      * chars
      * y inclusive
      * auto -1 if x>y
      * non-correct are left untouched
      * ${ is not brace expansion, inhibit
      * remove braces

      * mkdir /usr/local/src/bash/{old,new,dist,bugs}
      * chown root /usr/{ucb/{ex,edit},lib/{ex?.?*,how_ex}}
    * 0 prefix                                            `"%0...d"`            CHECK

  * tilde
    * tilde prefix
      * login name
      * not login or expansion fails -> untouched
    * null string -> $HOME
      * HOME unset -> home dir (as per /et/passwd?)
    * ~[N]+
    * ~[N]-
    * ~N
    * automatic expansion on assignment

  * parameter/variable
    * explodes words if "$@" or "${name[@]}"
    * $/${}                                               use f-strings         DONE
    * ${parameter}                                        `%(parameter)s`       DONE
    * ${!parameter}                                       `globals()[parameter]`, `locals()[parameters]`
                                                                                DONE
      * tilde, parameter, command, arithmetic                                   CHECK
      * nameref                                           `%(nameref)`          DONE
    * word
      * tilde, parametr, command, arithmetic
    * ${parameter:-word}
    * ${parameter:=word}
    * ${parameter:?word}
    * ${parameter:+word}
    * ${parameter:offset}                                 `parameter[offset:]`  DONE
    * ${parameter:offset:length}                          `parameter[offset:offset+length]`
                                                                                DONE
      * python offers more consistency and flexiblility   `parameter[start:end]`, `parameter[:end]`
      * arrays                                                                  DONE
      * undefined on dicts                                exception             CHECK
    * ${!prefix*}                                                               MAYBE
    * ${!name[@]}                                         `name.keys()`         DONE
    * ${#parameter}                                       `len(name)`           DONE
      * even for array lengths
    * ${parameter#word}

  * command substitution (LtR)
  * arithmetic
  * word splitting
    * explodes words
  * pathname
    * explodes words
  * process (in any of tilde, parameter, arithmetic, command)
  * quote removal                                                               WONTDO




  * +=                                                    `+=`, `.append()`     DONE

  * alias                                                 define function       WONTDO
  * declare                                                                     WONTDO
  * export                                                                      CHECK
  * local                                                 `local`               DONE
  * global                                                `global`              DONE
  * read
    * read -a
  * readonly                                                                    WONTDO
  * typeset                                                                     WONTDO
  * unset                                                 `del`                 DONE
