# ghost-to-mdx
> A tool to convert Ghost export files to a series of .MDX files.

[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)
![GitHub issues](https://img.shields.io/github/issues/Sealjay/ghost-to-mdx)
![GitHub](https://img.shields.io/github/license/Sealjay/ghost-to-mdx)
![GitHub Repo stars](https://img.shields.io/github/stars/Sealjay/ghost-to-mdx?style=social)
[![Python](https://img.shields.io/badge/--3178C6?logo=python&logoColor=ffffff)](https://www.python.org/)

## Overview
Ghost is an incredible project, but it's very expensive to run, with overhead for single user blogs. As Ghost develops over time, it's adding a lot of extra functionality around things like email subscriptions, and newsletters.

For some people, this functionality is too much.

This project is a tool to convert your Ghost export file into a series of .MDX files, which can be used with a static site generator, to be deployed to an [Azure Static Web App](https://docs.microsoft.com/en-us/azure/static-web-apps/deploy-nextjs?WT.mc_id=AI-MVP-5004204); reducing cost and maintenance complexity.


## Licensing
ghost-to-mdx is available under the [MIT Licence](./LICENCE).and is freely available to End Users.

## Solutions Referenced
- [Azure Static Web App](https://docs.microsoft.com/en-us/azure/static-web-apps/deploy-nextjs?WT.mc_id=AI-MVP-5004204)
- [Azure Static Web App CLI](https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/with-web-app/static-web-app-with-swa-cli/introduction?WT.mc_id=AI-MVP-5004204)

## Getting started with this repository
You can use a [dev container](https://docs.microsoft.com/en-us/azure-sphere/app-development/container-build-vscode?&WT.mc_id=AI-MVP-500420) to run this in VS Code, or in [GitHub codespaces](https://github.com/features/codespaces).


### Install the required python dependencies
This project uses Conda for managing dependencies, but you can use the requirements.txt file to install the dependencies using pip.

1. Update conda: `conda update conda`
2. Create the environment (Call it ghosttomdx) `conda create -c conda-forge -n ghosttomdx python=3.10 pip`
3. Activate the environment: `source activate ghosttomdx`
4. Install all required packages: `pip install -r requirements.txt`.
5. Get some space back: `conda clean -a`

### Run the python application

- `convert_ghost_to_html.py` will export flat-file HTML for posts and pages, along with metadata in YAML files.
- `convert_ghost_to_mdx.py` will export MDX and HTML suitable for use in a NextJS static site.

### Modifying the templates
MDX templates are found in the `data` folder, and follow the examples on the [NextJS](https://nextjs.org/docs/advanced-features/using-mdx) website.

## Contact
Feel free to contact me [on Twitter](https://twitter.com/sealjay_clj). For bugs, please [raise an issue on GitHub](https://github.com/Sealjay/ghost-to-mdx/issue).

## Contributing
Contributions are more than welcome! This repository uses [GitHub flow](https://guides.github.com/introduction/flow/) - with [Commitizen](https://github.com/commitizen/cz-cli#making-your-repo-commitizen-friendly) to enforce semantic commits (`npm install -g commitizen cz-customizable`, `echo '{ "path": "cz-customizable" }' > ~/.czrc`, and then `git cz`- easy to setup!)

**Note: This adds a .czrc file to your home directory, and will overwrite existing commitzen .czrc files.**