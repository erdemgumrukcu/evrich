# evrich

## Description

**evrich** is a cloud service available within the microservice-based grid automation platform **SOGNO**, designed to address the question of "where to charge" in distribution grids with multiple charging locations. It provides an application programming interface (API) that allows EV drivers to input their charging preferences, including search space, target state-of-charge, and parking period. In response, evrich identifies available charging spots in the specified area, gathers offers from charging station operators, and directs the EV driver to the optimal option based on the current situation. The current optimization approach in evrich focuses on minimizing charging costs for drivers [1]. However, its modular architecture allows for the integration of alternative strategies.

To effectively simulate interactions between the **evrich** service and external systems, a dynamic infrastructure has been developed. This setup automates request dispatch to the service based on predefined scenarios and logs the corresponding responses. Within this framework, the availability and charging commitments of charging stations in the test scenarios are modeled using datafev objects. *datafev* is a Python library specifically designed for developing and testing management algorithms for electric vehicles [2].

To enhance the flexibility of the test framework for incorporating numerous charging locations, the generation of Docker Compose files has been automated. The newly developed tool, *docker-compose-prepper*, streamlines this process. This automation is crucial for configuring both internal dependencies (containers within the **SOGNO** platform) and external dependencies (*datafev* objects representing charging stations). As a result, the test environment becomes more dynamic and scalable, efficiently accommodating a wide range of scenarios.

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

Docker-compose-prepper requires at least the following Python packages:

- pandas >= 2.0.3
- pyyaml >= 6.0.1
- openpyxl >= 3.1.2

## Usage

### Testing of evrich Service (Windows)

1. User may start with reshaping input files under `PATH-TO-DIRECTORY/external/event_manager/data_handling/input.xlsx`, `PATH-TO-DIRECTORY/external/utils/input.xlsx` and `PATH-TO-DIRECTORY/sogno/utils/input.xlsx` with the desired scenario data. These input files should be exactly identical.
2. Docker-compose-prepper scripts located at `PATH-TO-DIRECTORY/external/utils/prep_docker_compose.py` and `PATH-TO-DIRECTORY/sogno/utils/prep_docker_compose.py` should both be run.
3. In Windows PowerShell `docker-compose build` should be executed under both external(`PATH-TO-DIRECTORY/evrich/external`) and SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) directories.
4. Only for the first time, again in Windows PowerShell, `docker-compose up` should be first executed under external(`PATH-TO-DIRECTORY/evrich/external`) and then under SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) directory. This is due to the need to identify external networks to the SOGNO.
5. The building of the cloud-testing infrastructure of evrich service has been completed. The user should first execute `docker-compose up` command under SOGNO(`PATH-TO-DIRECTORY/evrich/sogno`) and afterwards under external(`PATH-TO-DIRECTORY/evrich/external`) directory in Windows PowerShell.
6. The output data will be saved under `PATH-TO-DIRECTORY/datafev/outputs`

## References

1. Gümrükçü, E., Klemets, J. R. A., Suul, J. A., Ponci, F., & Monti, A. (2022). Decentralized energy management concept for urban charging hubs with multiple V2G aggregators. IEEE Transactions on Transportation Electrification. IEEE.
2. Gumrukcu, E., Ahmadifar, A., Yavuzer, A., Ponci, F., & Monti, A. (2023). datafev—A Python framework for development and testing of management algorithms for electric vehicle charging infrastructures. *Software Impacts, 15*, 100467. Elsevier.

## Contact

- Aytug Yavuzer, M.Sc. <aytug.yavuzer@eonerc.rwth-aachen.de>
- Florian Oppermann, M.Sc. <florian.oppermann@eonerc.rwth-aachen.de>
- Erdem Gumrukcu, M.Sc. <erdem.guemruekcue@eonerc.rwth-aachen.de>
- Univ.-Prof. Antonello Monti, Ph.D. <post_acs@eonerc.rwth-aachen.de>

[Institute for Automation of Complex Power Systems (ACS)](http://www.acs.eonerc.rwth-aachen.de) 
[E.ON Energy Research Center (E.ON ERC)](http://www.eonerc.rwth-aachen.de) 
[RWTH Aachen University, Germany](http://www.rwth-aachen.de)
