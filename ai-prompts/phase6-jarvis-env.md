Jarvis environments capture a variety of common environment variables and store them within a pipeline.

## Build an environment

```
jarvis ppl env build ENV1=VAL1 ENV2=VAL2 ...
```

This will parse the remainder arguments for any additional parameters the user may expect.

This will edit the pipelines env.yaml file

At minimum, the environment variables will be:
```
CMAKE_MODULE_PATH
CMAKE_PREFIX_PATH
CPATH
JAVA_HOME
LD_LIBRARY_PATH
LIBRARY_PATH
PATH
PYTHONPATH
```

If there are any other common environment variables you can think of, please add them here.

## Build a named environment

Named environments store environment variables across pipelines in the config directory under a folder named env.

```
jarvis env build [env_name] ENV1=VAL1 ENV2=VAL2 ...
```

## Copy a named environment
```
jarvis ppl env copy [env_name]
```
