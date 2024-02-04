# evrich

## Description
evrich is a cloud service available in the microservice-based grid automation platform SOGNO that addresses the question of "where to charge" in distribution grids with multiple charging locations. It exposes an application programming interface to the users. The EV drivers can post their charging preferences, indicating a search space, target state-of-charge, and parking period. In return, evrich searches the available charging spots in the specified area, collects offers from the charging station operators, and instructs the EV driver to the best option under the given situation. The current optimization approach in the evrich prioritizes charging cost minimization for the drivers. However, its modular architecture allows for the integration of alternative approaches.

TODO: The cloud service is also ready for in-the-loop-testings.
## Contribution

1. Clone repository via SSH (`git clone git@git.rwth-aachen.de:acs/public/automation/evrich.git`) or clone repository via HTTPS (`git clone https://git.rwth-aachen.de/acs/public/automation/evrich.git`)
2. Open an issue at [https://git.rwth-aachen.de/acs/public/automation/evrich/issues](https://git.rwth-aachen.de/acs/public/automation/evrich/issues)
3. Checkout the development branch: `git checkout development` 
4. Update your local development branch (if necessary): `git pull origin development`
5. Create your feature/issue branch: `git checkout -b issueXY_explanation`
6. Commit your changes: `git commit -m "Add feature #XY"`
7. Push to the branch: `git push origin issueXY_explanation`
8. Submit a pull request from issueXY_explanation to development branch via [https://git.rwth-aachen.de/acs/public/automation/evrich/pulls](https://git.rwth-aachen.de/acs/public/automation/evrich/pulls)
9. Wait for approval or revision of the new implementations.

## Installation
Docker Desktop installation is essential to use evrich, which can be downloaded from: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

To maximize the flexibility of the test framework in terms of incorporating a large number of charge locations, the docker-compose generation process was automated. The developed software docker-compose-prepper automates the process of generating docker-compose files, which are required to configure both internal (containers within the SOGNO platform) and external (datafev objects representing the interacted charging stations) dependencies of a dynamic test environment. Docker-compose-prepper requires at least the following Python packages:
- pandas >= 2.0.3
- pyyaml >= 6.0.1
- openpyxl >= 3.1.2

## Usage
### evrich Service
TODO

### Cloud Testing of evrich Service (Windows)
1. User may start with reshaping input files under `PATH-TO-DIRECTORY/external/event_manager/data_handling/input.xlsx`, `PATH-TO-DIRECTORY/external/utils/input.xlsx` and `PATH-TO-DIRECTORY/sogno/utils/input.xlsx` with the desired scenario data. These input files should be exactly identical.
2. Docker-compose-prepper scripts located at external/utils/prep_docker_compose.py and sogno/utils/prep_docker_compose.py should both be run.
3. In Windows PowerShell `docker-compose build` should be executed under both external(`PATH-TO-DIRECTORY/evrich/external`) and SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) directories.
4. Only for the first time, again in Windows PowerShell, `docker-compose up` should be first executed under external(`PATH-TO-DIRECTORY/evrich/external`) and then under SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) directory. This is due to the need to identify external networks to the SOGNO.
5. The building of the cloud-testing infrastructure of evrich service has been completed. The user should first execute `docker-compose up` command under SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) and afterwards under external(`PATH-TO-DIRECTORY/evrich/external`) directory in Windows PowerShell.
6. The output data will be saved under `PATH-TO-DIRECTORY/datafev/outputs`

## Contact
- Erdem Gumrukcu, M.Sc. <erdem.guemruekcue@eonerc.rwth-aachen.de>
- Florian Oppermann, M.Sc. <florian.oppermann@eonerc.rwth-aachen.de>
- Aytug Yavuzer, M.Sc. <aytug.yavuzer@eonerc.rwth-aachen.de>
- Univ.-Prof. Antonello Monti, Ph.D. <post_acs@eonerc.rwth-aachen.de>

[Institute for Automation of Complex Power Systems (ACS)](http://www.acs.eonerc.rwth-aachen.de) \
[E.ON Energy Research Center (E.ON ERC)](http://www.eonerc.rwth-aachen.de) \
[RWTH Aachen University, Germany](http://www.rwth-aachen.de)

