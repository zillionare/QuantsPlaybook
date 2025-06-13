1. 请使用python 3.12，允许使用所有的开源python库。
2. 数据源使用tushare和akshare（优先使用tushare），以及其它可靠的免费数据源。当需要使用akshare时，请使用这个token: ce9f8c37a4af987f6328321ed4b3f9379f695d6d6bdc5b59d454e3ad
3. 将.ipynb中使用jqdata或者其它聚宽数据源的部分，改造成为使用tushare或者akshare，但保持功能不变，结论不变
4. 新移植的版本使用与原文一样的名字，但增加-ported后缀。比如如果原文是APM因子模型.ipynb，则移植后的文件名为APM因子模型-ported.ipynb，都存放在同一目录。
5. 在改造时，如果在进行因子分析，请使用alphalens-reloaded这个库，如果要显示策略评估指标，请使用quantstats，以增加文章的可读性，保持代码精练、简洁。
6. 上述改造可能导致无法一对一替换原文的单元格，在此情况下，请尊重原文思想和结论，可以采用适当的代码结构。
