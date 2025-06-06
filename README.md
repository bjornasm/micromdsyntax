micromdsyntax is a tool that generates a custom YAML syntax file for the [Micro editor](https://micro-editor.github.io/) to enable syntax highlighting within fenced Markdown code blocks. 

It collects and integrates syntax definitions for multiple programming languages directly from Micro’s official repository or from local copies of its YAML syntax files.

[The resulting file](https://github.com/bjornasm/micromdsyntax/blob/master/yamlfiles/markdownsyntaxhighlight.yaml) extends Micro's Markdown highlighting to support embedded fenced code blocks.

Give it a try, run the code with `uv run main.py` or download the resulting yaml file and add it to `~/.config/micro/syntax/` then copy the following into a markdown file with Micro:

````markdown
```python
def greet():
    for i in range(10):
        print(f"Hello World, {i}!")
```

```javascript
function greet() {
    for (let i = 0; i < 10; i++) {
        console.log(`Hello World, ${i}!`);
    }
}
```

```java
public class Main {
    public static void greet() {
        for (int i = 0; i < 10; i++) {
            System.out.println("Hello World, " + i + "!");
        }
    }
}
```

```c
#include <stdio.h>

void greet() {
    for (int i = 0; i < 10; i++) {
        printf("Hello World, %d!\n", i);
    }
}
```

```cpp
#include <iostream>

void greet() {
    for (int i = 0; i < 10; i++) {
        std::cout << "Hello World, " << i << "!" << std::endl;
    }
}
```

```ruby
def greet
  10.times do |i|
    puts "Hello World, #{i}!"
  end
end
```

```go
package main
import "fmt"

func greet() {
    for i := 0; i < 10; i++ {
        fmt.Printf("Hello World, %d!\n", i)
    }
}
```

```sh
greet() {
    for i in {0..9}
    do
        echo "Hello World, $i!"
    done
}
```

```powershell
function greet {
    for ($i = 0; $i -lt 10; $i++) {
        Write-Output "Hello World, $i!"
    }
}
```

```php
<?php
function greet() {
    for ($i = 0; $i < 10; $i++) {
        echo "Hello World, $i!\n";
    }
}

greet();
?>
```
````
