
class Simulation(object):
    """
    Simulation object to be created from XLSX inputs.
    """

    def __init__(self, start, end, step, horizon, service_fleet):
        """
        Simulation class initializer.

        Parameters
        ----------
        start : datetime
            Start date time of the simulation.
        end : datetime
            End date time of the simulation.
        step : timedelta
            Simulation step time delta (to be given in minutes).
        service_fleet : pandas dataframe 
            EV fleet to use service and their behavior indexed with timeseries.

        Returns
        -------
        None.

        """
        # TODO: eger tou_tariff, fleet timedeltasi girilen timedeltayla(genel olarak zaman girdileri) uyusmazsa raise error ver
        self.start = start
        self.end = end
        self.step = step
        self.horizon = horizon
        self.service_fleet = service_fleet
