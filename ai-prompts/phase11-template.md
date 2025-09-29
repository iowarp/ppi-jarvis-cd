Add a method called copy_template_file to the Pkg class, which copies a file from one location to
another. It replaces constants in the file using a format. It looks like this:
 
It should be used like this:

```python
self.copy_template_file(f'{self.pkg_dir}/config/hermes.xml',
                                    self.adios2_xml_path,
                                    replacements={
                                        'PPN': 1
                                    })
```

The constants have the following structure:
```
<parameter key="ppn" value='##PPN##'/> 
```

So it would look like this in the result file:
```
<parameter key="ppn" value='1'/> 
```
