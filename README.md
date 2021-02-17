# lazyprofiler
[![TravisCI](https://img.shields.io/travis/shankarpandala/lazyprofiler.svg)](https://travis-ci.org/shankarpandala/lazyprofiler)
[![CircleCI](https://circleci.com/gh/shankarpandala/lazyprofiler.svg?style=svg)](https://circleci.com/gh/shankarpandala/lazyprofiler)
[![CodeCov](https://codecov.io/gh/shankarpandala/lazyprofiler/branch/master/graph/badge.svg)](https://codecov.io/gh/shankarpandala/lazyprofiler)
[![Downloads](https://pepy.tech/badge/lazyprofiler)](https://pepy.tech/project/lazyprofiler)
-------------------------------------------

Lazy Profiler is a simple utility to collect CPU, GPU, RAM and GPU Memory stats while the program is running.


## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install lazyprofiler
```

## Usage

```python
import lazyprofiler.GetStats as gs
pid = gs.start_log("test")
"""
Do something in between
"""
gs.stop_log(pid=pid)
gs.plot_stats('test')
```
![Sample Output](/images/sample.PNG)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
