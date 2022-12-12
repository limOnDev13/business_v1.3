import numpy as np
import matplotlib.pyplot as plt
import datetime as date
import copy
from ctypes import *


class DistributionParameters():
    # среднеквадратичное отклонение
    scale = 0
    # средний коэффициент массонакопления
    massAccumulationCoefficient = 0
    # количество рыб
    amountFishes = 0
    # массив значений, которые распределены по Гауссу в заданных параметрах
    _gaussValues = []

    def __init__(self, amountFishes,
                 scale=0.003,
                 massAccumulationCoefficientMin=0.07,
                 massAccumulationCoefficientMax=0.087):
        self.massAccumulationCoefficient = (massAccumulationCoefficientMin +
                                       massAccumulationCoefficientMax) / 2
        self.amountFishes = amountFishes
        self.scale = scale
        self._make_gaussian_distribution()

    def _make_gaussian_distribution(self):
        self._gaussValues = np.random.normal(self.massAccumulationCoefficient,
                                        self.scale,
                                        self.amountFishes)
        self._gaussValues.sort()

    def draw_hist_distribution(self, numberFishInOneColumn):
        plt.hist(self._gaussValues, numberFishInOneColumn)
        plt.show()

    def return_array_distributed_values(self):
        return self._gaussValues


def assemble_array(array, amountItems, index):
    result = (c_float * amountItems)()
    for i in range(amountItems):
        result[i] = array[i][index]
    return result


class FishArray():
    _amountFishes = 0
    _arrayFishes = list()
    _biomass = c_float()
    # массив покупок мальков
    _arrayFryPurchases = list()
    _feedRatio = 1.5
    _dllBuisnessPlan = 0


    def __init__(self, feedRatio=1.5):
        self._feedRatio = c_float(feedRatio)
        self._biomass = c_float()
        self._amountFishes = 0
        self._arrayFishes = list()
        self._arrayFryPurchases = list()
        self._dllBuisnessPlan = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def add_biomass(self, date, amountFishes, averageMass):
        # создаем параметры для нормального распределения коэффициентов массонакопления
        distributionParameters = DistributionParameters(amountFishes)
        arrayCoefficients = distributionParameters.return_array_distributed_values()

        # закидываем информацию о новой биомассе в массив
        for i in range(amountFishes):
            # ноль означает (количество дней в бассике, но это не точно
            # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass],...]
            self._arrayFishes.append([averageMass, arrayCoefficients[i], averageMass])
            self._arrayFryPurchases.append([date, amountFishes, averageMass])

        # увеличиваем количество рыбы в бассейне
        self._amountFishes += amountFishes
        # так как все в граммах, то делим на 1000, чтобы получить килограммы в биомассе
        self._biomass.value += amountFishes * averageMass / 1000

    def add_other_FishArrays(self, fishArray):
        amountNewFishes = len(fishArray)

        # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass]
        for i in range(amountNewFishes):
            self._biomass.value = self._biomass.value + fishArray[i][2] / 1000
            self._arrayFishes.append(fishArray[i])
        self._amountFishes += amountNewFishes

    def _sort_fish_array(self):
        self._arrayFishes.sort(key=lambda x: x[2])

    def remove_biomass(self, amountFishToRemove):
        self._sort_fish_array()
        removedFishes = list()
        for i in range(amountFishToRemove):
            fish = self._arrayFishes.pop(self._amountFishes - amountFishToRemove)
            removedFishes.append(fish)
            # уменьшаем биомассу
            self._biomass.value -= fish[2] / 1000
        # уменьшаем количество рыб
        self._amountFishes -= amountFishToRemove
        return removedFishes

    def daily_work(self):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.daily_work

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float)]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        dailyFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass))

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return dailyFeedMass

    def do_daily_work_some_days(self, amountDays):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.do_daily_work_some_days

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float), c_int]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        totalFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass), amountDays)

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return totalFeedMass

    def get_amount_fishes(self):
        return self._amountFishes

    def get_array_fish(self):
        return self._arrayFishes

    def calculate_when_fish_will_be_sold(self, massComercialFish,
                                         singleVolume, fishArray):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllBuisnessPlan.calculate_when_fish_will_be_sold

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_float, c_int]
        calculateLib.restype = c_int

        amountFish = len(fishArray)
        biomass = 0
        for i in range(amountFish):
            biomass += fishArray[i][2] / 1000
        biomass = c_float(biomass)

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(fishArray, amountFish, 2)
        arrayMassAccumulationCoefficient = assemble_array(fishArray,
                                                          amountFish, 1)

        amountDays = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                  amountFish, self._feedRatio,
                                  byref(biomass), massComercialFish,
                                  singleVolume)

        for i in range(amountFish):
            fishArray[i][2] = arrayMass[i]

        return amountDays

    def calculate_difference_between_number_growth_days_and_limit_days(self, massComercialFish, singleVolume,
                                                                       maxDensity, square):
        calculateLib = self._dllBuisnessPlan.calculate_how_many_fish_needs

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 POINTER(c_float), c_int, c_float,
                                 POINTER(c_float),  POINTER(c_float),
                                 c_float, c_int, c_float, c_float,
                                 POINTER(c_int)]
        calculateLib.restype = c_int

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass1 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMass2 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)
        resultAmountsDays = (c_int * 2)(0)

        biomass1 = c_float(0.0)
        biomass2 = c_float(0.0)

        for i in range(self._amountFishes):
            biomass1.value += arrayMass1[i] / 1000
            biomass2.value += arrayMass1[i] / 1000

        amountDays = calculateLib(arrayMass1, arrayMass2, arrayMassAccumulationCoefficient,
                                  self._amountFishes, self._feedRatio,
                                  byref(biomass1), byref(biomass2), massComercialFish,
                                  singleVolume, maxDensity, square, resultAmountsDays)

        return [amountDays, resultAmountsDays[0], resultAmountsDays[1]]
    def calculate_average_mass(self):
        if (self._amountFishes != 0):
            result = self._biomass.value / self._amountFishes * 1000
        else:
            result = 0.0
        return result

    def get_biomass(self):
        return self._biomass.value


class Pool():
    square = 0
    maxPlantingDensity = 0
    arrayFishes = 0
    # количество мальков в 1 упаковке
    singleVolumeFish = 0
    # цена на мальков
    costFishFry = [[5, 35],
                   [10, 40],
                   [20, 45],
                   [30, 50],
                   [50, 60],
                   [100, 130]]
    # массив, в котором хранится информация о покупке мальков
    arrayFryPurchases = list()
    # массив, в котором хранится информация о продаже рыбы
    arraySoldFish = list()
    # текущая плотность посадки
    currentDensity = 0
    # массив кормежек
    feeding = list()
    # масса товарной рыбы
    massComercialFish = 350
    # цена рыбы
    price = 1000
    # индекс зарыбления
    indexFry = 0
    # начальная масса зарыбления
    startMass = 0
    procentOnDepreciationEquipment = 10


    def __init__(self, square, startMass, singleVolumeFish=100, price=1000,
                 massComercialFish=350,
                 maximumPlantingDensity=40):
        self.square = square
        self.startMass = startMass
        self.massComercialFish = massComercialFish
        self.maxPlantingDensity = maximumPlantingDensity
        self.singleVolumeFish = singleVolumeFish
        self.arrayFishes = FishArray()
        self.feeding = list()
        self.arrayFryPurchases = list()
        self.arraySoldFish = list()
        self.price = price

    def add_new_biomass(self, amountFishes, averageMass, newIndex, date):
        self.indexFry = newIndex
        self.arrayFishes.add_biomass(date, amountFishes, averageMass)
        # сохраним инфо о покупки мальков
        # arrayFryPurchases[i] = [date, amountFries, averageMass, totalPrice]
        totalPrice = 0
        for i in range(len(self.costFishFry)):
            if (averageMass < self.costFishFry[i][0]):
                totalPrice = amountFishes * self.costFishFry[i][1]
        self.arrayFryPurchases.append([date, amountFishes, averageMass, totalPrice])
        self.currentDensity = amountFishes * (averageMass / 1000) / self.square

    def daily_growth(self, day):
        todayFeedMass = self.arrayFishes.daily_work()
        # сохраняем массы кормежек
        self.feeding.append([day, todayFeedMass])

        # проверяем, есть ли рыба на продажу, и если есть - продаем
        self.sell_fish(day)

    def sell_fish(self, day):
        amountFishForSale = 0
        for i in range(self.arrayFishes.get_amount_fishes()):
            if (self.arrayFishes.get_array_fish()[i][2] >= self.massComercialFish):
                amountFishForSale += 1

        if ((amountFishForSale >= self.singleVolumeFish) or
                ((amountFishForSale == self.arrayFishes.get_amount_fishes()) and
                 (self.arrayFishes.get_amount_fishes() != 0))):
            print('Изначальная биомасса ', self.arrayFishes.get_biomass())
            soldFish = self.arrayFishes.remove_biomass(amountFishForSale)
            # продаем выросшую рыбу и сохраняем об этом инфу
            soldBiomass = 0
            amountSoldFish = 0
            for i in range(len(soldFish)):
                soldBiomass += soldFish[i][2] / 1000
                amountSoldFish += 1

            print(day, ' продано биомассы: ', soldBiomass)
            revenue = soldBiomass * self.price

            self.arraySoldFish.append([day, amountSoldFish, soldBiomass, revenue])
            # обновим density
            self.currentDensity = self.arrayFishes.get_biomass() / self.square

    def update_density(self):
        self.currentDensity = self.arrayFishes.get_biomass() / self.square

    def calculate_difference_between_number_growth_days_and_limit_days(self, amountFishForSale):
        testFishArray = copy.deepcopy(self.arrayFishes)
        amountDays = testFishArray.calculate_difference_between_number_growth_days_and_limit_days\
            (self.massComercialFish,
             amountFishForSale,
             self.maxPlantingDensity,
             self.square)
        return amountDays


class Module():
    costCWSD = 3000000
    amountPools = 0
    amountGroups = 0
    # температура воды
    temperature = 21
    # арендная плата
    rent = 70000
    # стоимость киловатт в час
    costElectricityPerHour = 3.17
    # мощность узв
    equipmentCapacity = 5.6
    # стоимость корма
    feedPrice = 260
    onePoolSquare = 0
    pools = list()
    salary = 50000
    amountWorkers = 2
    percentageIncomeOnDepreciationEquipment = 10
    feedings = list()
    fries = list()
    rents = list()
    salaries = list()
    elecrtricity = list()
    revenues = list()
    arrayDepreciationEquipment = list()
    budget = list()
    amountModules = 0


    def __init__(self, poolSquare, masses, salary=50000, amountWorkers=2,
                 amountPools=8, amountGroups=4, fishPrice=1000,
                 feedPrice=260, equipmentCapacity=5.5, rent=70000,
                 costElectricityPerHour=3.17, temperature=21, percentageIncomeOnDepreciationEquipment=20,
                 costCWSD=3000000):
        self.costCWSD=3000000
        self.salary = salary
        self.percentageIncomeOnDepreciationEquipment = percentageIncomeOnDepreciationEquipment
        self.amountWorkers = amountWorkers
        self.onePoolSquare = poolSquare
        self.amountGroups = amountGroups
        self.amountPools = amountPools
        self.fishPrice = fishPrice
        self.temperature = temperature
        self.rent = rent
        self.costElectricityPerHour = costElectricityPerHour
        self.equipmentCapacity = equipmentCapacity
        self.feedPrice = feedPrice
        self.costCWSD = costCWSD
        self.pools = list()

        for i in range(amountPools):
            pool = Pool(poolSquare, masses[i])
            self.pools.append(pool)

        self.profit = list()
        self.feedings = list()
        self.fries = list()
        self.rents = list()
        self.salaries = list()
        self.elecrtricity = list()
        self.revenues = list()
        self.arrayDepreciationEquipment = list()
        self.budget = list()
        self.amountModules = int(self.amountPools / self.amountGroups)


    def add_biomass_in_pool(self, poolNumber, amountFishes, mass, newIndex, date):
        self.pools[poolNumber].add_new_biomass(amountFishes, mass, newIndex, date)

    def _calculate_technical_costs(self, startingDate, endingDate):
        deltaTime = endingDate - startingDate
        amountDays = deltaTime.days
        electrisityCost = amountDays * 24 * self.equipmentCapacity * self.costElectricityPerHour
        rentCost = (int(amountDays / 30)) * self.rent
        salaryCost = (int(amountDays / 30)) * self.salary * self.amountWorkers

        print('За этот период траты на аренду составят ', rentCost, 'p')
        print('Расходы на заработную плату составят ', salaryCost, 'p')
        print('Траты на электричество составят ', electrisityCost, 'p')

        return [rentCost, electrisityCost, rentCost + electrisityCost + salaryCost]

    def _calculate_cost_fry(self, startDate, endDate):
        costFry = 0
        for i in range(self.amountGroups):
            for j in range(len(self.pools[i].arrayFryPurchases)):
                # [date, amountFishes, averageMass, totalPrice]
                if (startDate <= self.pools[i].arrayFryPurchases[j][0] <= endDate):
                    costFry += self.pools[i].arrayFryPurchases[j][3]

        return costFry

    def _calculate_cost_feed(self, startDate, endDate):
        costFeed = 0
        for i in range(self.amountGroups):
            for j in range(len(self.pools[i].feeding)):
                if (startDate <= self.pools[i].feeding[j][0] <= endDate):
                    costFeed += self.pools[i].feeding[j][1]

        return costFeed

    def _calculate_biological_costs(self, startingDate, endingDate):
        feedMass = self._calculate_cost_feed(startingDate, endingDate)
        fryCost = self._calculate_cost_fry(startingDate, endingDate)

        feedCost = feedMass * self.feedPrice

        print('За этот период израсходуется ', feedMass, ' кг корма, расходы на корм составят ', feedCost, 'p')
        print('Будет куплено малька на ', fryCost, 'p')

        return [feedCost, fryCost, feedCost + fryCost]

    def _calculate_sold_biomass_and_revenue(self, startDate, endDate):
        soldBiomass = 0
        amountSoldFish = 0
        revenue = 0
        for i in range(self.amountGroups):
            # [day, amountSoldFish, soldBiomass, revenue]
            for j in range(len(self.pools[i].arraySoldFish)):
                if (startDate <= self.pools[i].arraySoldFish[j][0] <= endDate):
                    amountSoldFish += self.pools[i].arraySoldFish[j][1]
                    soldBiomass += self.pools[i].arraySoldFish[j][2]
                    revenue += self.pools[i].arraySoldFish[j][3]
        return [soldBiomass, revenue, amountSoldFish]

    def move_fish_from_one_pool_to_another(self, onePoolNumber, anotherPoolNumber, amountMovedFish):
        # удалим выросшую рыбу из старого бассейна
        removedFish = self.pools[onePoolNumber].arrayFishes.remove_biomass(amountMovedFish)
        # обновим плотность
        self.pools[onePoolNumber].update_density()
        # добавим удаленную рыбу в другой бассейн
        self.pools[anotherPoolNumber].arrayFishes.add_other_FishArrays(removedFish)
        # обновим плотность в другом бассейне
        self.pools[anotherPoolNumber].update_density()
        # теперь в новом бассейне плавает малек с индексом из предыдущего басса
        self.pools[anotherPoolNumber].indexFry = self.pools[onePoolNumber].indexFry

    def total_daily_work(self, day):
        for i in range(self.amountPools):
            self.pools[i].daily_growth(day)

    def print_info(self, amoutItemes):
        print()
        for i in range(self.amountGroups):
            print('№', i, ' pool, indexFry = ', self.pools[i].indexFry, ', amountFish = ',
                  self.pools[i].arrayFishes.get_amount_fishes(),
                  ', biomass = ', self.pools[i].arrayFishes.get_biomass(),
                  ', averageMass = ', self.pools[i].arrayFishes.calculate_average_mass())
            result = ''
            if (self.pools[i].arrayFishes.get_amount_fishes() != 0):
                # выпишем данные о первых amoutItemes рыбках
                for j in range(amoutItemes):
                    result += str(self.pools[i].arrayFishes.get_array_fish()[j])
            else:
                result += 'Рыбы нет'
            print(result)
        print('___________________________________')

    def find_optimal_fry_mass(self, minMass, deltaMass):
        minAverageMass = 10000
        for i in range(self.amountGroups):
            if (minAverageMass > self.pools[i].arrayFishes.calculate_average_mass()):
                minAverageMass = self.pools[i].arrayFishes.calculate_average_mass()

        result = (int((minAverageMass - deltaMass) / 10)) * 10
        if (result < minMass):
            result = minMass

        return result

    def find_empty_pool_and_add_one_volume(self, volumeFish, newIndex, day):
        maxAverageMass = 0
        emptyPool = 0
        for i in range(self.amountGroups):
            if ((self.pools[i].arrayFishes.get_amount_fishes() == 0) and
                    (self.pools[i].startMass > maxAverageMass)):
                maxAverageMass = self.pools[i].startMass
                emptyPool = i

        optimalMass = self.find_optimal_fry_mass(20, 20)
        self.pools[emptyPool].add_new_biomass(volumeFish, optimalMass, newIndex, day)

        print('Добавим ', volumeFish, ' штук рыбы в ', emptyPool, ' бассейн  ', day)
        self.print_info(3)
        print()

    def find_empty_pool_and_add_twice_volume(self, volumeFish, newIndex, day):
        emptyPool = 0
        for i in range(self.amountGroups):
            if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                emptyPool = i
                break

        optimalMass = self.find_optimal_fry_mass(20, 20)
        self.pools[emptyPool].add_new_biomass(2 * volumeFish, optimalMass, newIndex, day)

        print('Добавим ', 2 * volumeFish, ' штук рыбы в ', emptyPool, ' бассейн  ', day)
        self.print_info(3)
        print()

    def find_pool_with_twice_volume_and_move_half_in_empty(self, day):
        overflowingPool = 0
        emptyPool = 0
        maxAmount = 0
        volumeFish = 0
        maxAverageMass = 0
        for i in range(self.amountGroups):
            if (self.pools[i].arrayFishes.get_amount_fishes() > maxAmount):
                overflowingPool = i
                maxAmount = self.pools[i].arrayFishes.get_amount_fishes()

            volumeFish = int(maxAmount / 2)

            if ((self.pools[i].arrayFishes.get_amount_fishes() == 0) and
                    (maxAverageMass < self.pools[i].startMass)):
                emptyPool = i
                maxAverageMass = self.pools[i].startMass

        self.move_fish_from_one_pool_to_another(overflowingPool, emptyPool, volumeFish)

        print('Переместим из ', overflowingPool, ' бассейна в ', emptyPool,
              ' бассейн ', volumeFish, ' штук рыбы', day)
        self.print_info(3)
        print()

    def grow_up_fish_in_one_pool(self, startDay):
        flag = True
        day = startDay

        while (flag):
            self.total_daily_work(day)
            day += date.timedelta(1)
            for i in range(self.amountGroups):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    flag = False
                    break

        print('Вырастим и продадим всю рыбу в одном бассейне', day)
        self.print_info(3)
        print()

        return day

    def grow_up_fish_in_two_pools(self, startDay):
        flag = True
        day = startDay

        while(flag):
            self.total_daily_work(day)
            day += date.timedelta(1)

            amountEmptyFools = 0
            for i in range(self.amountGroups):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    amountEmptyFools += 1

            if (amountEmptyFools == 2):
                flag = False

        print('Вырастим и продадим всю рыбу в двух бассейнах', day)
        self.print_info(3)
        print()

        return day

    def start_script1(self, masses, reserve, startDate):
        optimization = Opimization()
        optimalQuantity = optimization.calculate_optimized_amount_fish_in_commercial_pool(self.onePoolSquare,
                                                                                          masses[self.amountGroups - 1],
                                                                                          masses[self.amountGroups - 1],
                                                                                          10, 10)
        mainVolumeFish = optimalQuantity[0]
        mainVolumeFish -= reserve

        for i in range(self.amountGroups - 1):
            self.pools[i].add_new_biomass(mainVolumeFish, masses[i], i, startDate)
        # в бассейн с самой легкой рыбой отправляем в 2 раза больше
        self.pools[self.amountGroups - 1].indexFry = self.amountGroups - 1
        self.pools[self.amountGroups - 1].add_new_biomass(2 * mainVolumeFish, masses[self.amountGroups - 1],
                                                          self.amountGroups - 1, startDate)

        day = startDate
        print('Начинаем ', day, ' c таким зарыблением')
        self.print_info(3)
        print()

        # вырастим рыбу в 0 бассейне
        day = self.grow_up_fish_in_one_pool(day)

        # переместим рыбу из 3 в 0 бассейн
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day)

        currentIndex = 4

        # добавим рыбу 2 * mainValue в 1 бассейн
        self.find_empty_pool_and_add_twice_volume(mainVolumeFish, currentIndex, day)
        currentIndex += 1

        # вырастим рыбу в 2 бассейне
        day = self.grow_up_fish_in_one_pool(day)

        return [mainVolumeFish, day, currentIndex]

    def main_script1(self, mainValue, day, previousIndex):
        # переместим из переполненного бассейна в пустой половину
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day)

        currentIndex = previousIndex
        # добавим mainValue штук рыб в пустой бассейн
        self.find_empty_pool_and_add_one_volume(mainValue, currentIndex, day)
        currentIndex += 1

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day)
        currentIndex += 1

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day)

        # переместим из переполненного бассейна в пустой
        self.find_pool_with_twice_volume_and_move_half_in_empty(day)

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day)
        currentIndex += 1

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day)

        return [mainValue, day, currentIndex]

    def main_work1(self, startDate, endDate, masses, reserve):
        resultStartScript = self.start_script1(masses, reserve, startDate)
        print('Начинается main_script1 в 1 раз!!!!!!!!!!!!!!!!!!!!!!!!')
        print()
        day = resultStartScript[1]
        # [mainVolumeFish, day, currentIndex]
        resultMainScript = self.main_script1(resultStartScript[0],
                                             resultStartScript[1],
                                             resultStartScript[2])

        numberMainScript = 2
        while (day < endDate):
            print('Начинается main_script1 в ', numberMainScript, ' раз!!!!!!!!!!!!!!!!!!!!!!!!')
            print()
            numberMainScript += 1
            # [mainValue, day, currentIndex]
            resultMainScript = self.main_script1(resultMainScript[0],
                                                 resultMainScript[1],
                                                 resultMainScript[2])
            day = resultMainScript[1]

        # подсчетаем выручку, расходы и прибыль
        self.calculate_all_casts_and_profits_for_all_period(startDate, endDate)
        self.budget.append([startDate, -self.costCWSD])
        self.calculate_budget(startDate, endDate)

    def show_all_information_every_month(self, startDate, endDate):
        startMonth = startDate
        endMonth = self._calculate_end_date_of_month(startMonth)
        numberMonth = 1
        while (endMonth < endDate):
            bioCast_feed = self._calculate_something_in_certain_period(self.feedings, startMonth, endMonth)
            bioCast_fry = self._calculate_something_in_certain_period(self.fries, startMonth, endMonth)
            techCast_rent = self._calculate_something_in_certain_period(self.rents, startMonth, endMonth)
            techCast_salary = self._calculate_something_in_certain_period(self.salaries, startMonth, endMonth)
            techCast_electricity = self._calculate_something_in_certain_period(self.elecrtricity, startMonth, endMonth)
            techCast_depreciationEquipment = self._calculate_something_in_certain_period(
                self.arrayDepreciationEquipment,
                startMonth, endMonth)
            revenue = self._calculate_sold_biomass_and_revenue(startMonth, endMonth)
            profit = self._find_event_in_this_day(endMonth, self.budget)
            print('начало ', startMonth, 'конец ', endMonth, ' ', numberMonth, ' месяц')
            print('траты на технику (аренда, зарплата, електричество): ',
                  -(techCast_rent + techCast_salary + techCast_electricity))
            print('траты на мальков: ', -bioCast_fry)
            print('траты на корм: ', -bioCast_feed)
            print('Отложено на амортизацию оборудования: ', -techCast_depreciationEquipment)
            print('Все расходы: ', -(bioCast_feed + bioCast_fry + techCast_depreciationEquipment + techCast_rent +
                                     techCast_salary + techCast_electricity))
            print('За этот месяц будет продано: ', revenue[0], ' кг')
            print('Количество проданной рыбы: ', revenue[2])
            print('выручка составит: ', revenue[1])
            print('Бюджет на данный день составит: ', profit)
            print('_____________________________________________________________')
            numberMonth += 1
            startMonth = endMonth + date.timedelta(1)
            endMonth = self._calculate_end_date_of_month(startMonth) - date.timedelta(1)

    def _calculate_end_date_of_month(self, startDate):
        result = startDate
        while ((result.day != startDate.day) or
               (result.month == startDate.month)):
            result += date.timedelta(1)
        return result

    def _calculate_something_in_certain_period(self, array, startDate, endDate):
        result = 0
        for i in range(len(array)):
            if (startDate <= array[i][0] <= endDate):
                result += array[i][1]

        return result

    def calculate_all_casts_and_profits_for_all_period(self, startDate, endDate):
        for i in range(self.amountGroups):
            for j in range(len(self.pools[i].feeding)):
                # [day, todayFeedMass]
                self.feedings.append([self.pools[i].feeding[j][0],
                                      self.pools[i].feeding[j][1] * self.feedPrice])
            for j in range(len(self.pools[i].arrayFryPurchases)):
                # [date, amountFishes, averageMass, totalPrice]
                self.fries.append([self.pools[i].arrayFryPurchases[j][0],
                                  self.pools[i].arrayFryPurchases[j][3]])
            for j in range(len(self.pools[i].arraySoldFish)):
                # [day, amountSoldFish, soldBiomass, revenue]
                self.revenues.append([self.pools[i].arraySoldFish[j][0],
                                      self.pools[i].arraySoldFish[j][3]])

        startMonth = startDate
        endMonth = self._calculate_end_date_of_month(startMonth)
        while (endMonth <= endDate):
            self.rents.append([endMonth, self.rent])
            self.salaries.append([endMonth, self.amountWorkers * self.salary])
            amountDaysInThisMonth = (endMonth - startMonth).days
            self.elecrtricity.append([endMonth,
                                      amountDaysInThisMonth * 24 * self.equipmentCapacity])
            startMonth = endMonth
            endMonth = self._calculate_end_date_of_month(startMonth)

    def calculate_budget(self, startDate, endDate):
        day = startDate
        amountDays = (endDate - startDate).days
        amountItemsInBudeget = 1

        for i in range(amountDays):
            revenue = self._find_event_in_this_day(day, self.revenues)
            techCost = self._find_event_in_this_day(day, self.rents)
            techCost += self._find_event_in_this_day(day, self.salaries)
            techCost += self._find_event_in_this_day(day, self.elecrtricity)
            bioCost = self._find_event_in_this_day(day, self.feedings)
            bioCost += self._find_event_in_this_day(day, self.fries)
            self.budget.append([day, self.budget[amountItemsInBudeget - 1][1] + revenue - techCost - bioCost])

            if ((day.day == startDate.day) and (day.month == startDate.month) and (day.year != startDate.year)):
                x = self.budget[amountItemsInBudeget][1] * self.percentageIncomeOnDepreciationEquipment / 100
                self.budget[amountItemsInBudeget][1] -= x
                self.arrayDepreciationEquipment.append([day, x])
            day += date.timedelta(1)
            amountItemsInBudeget += 1

    def _find_event_in_this_day(self, day, array):
        result = 0
        for i in range(len(array)):
            if (array[i][0] == day):
                result += array[i][1]

        return result


class Opimization():
    _dllArrayFish = 0
    _dllPool = 0

    def __init__(self):
        self._dllPool = WinDLL("D:/github/buisnessPlan_v1.2.1/buisnessPlan_v1.2/dllPool/x64/Debug/dllPool.dll")
        self._dllArrayFish = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def calculate_optimized_amount_fish_in_commercial_pool(self, square, startMass, mass, startAmount, step):
        flagNumber = 0
        amountFish = startAmount
        amountGrowthDays = 0
        amountDaysBeforeLimit = 0

        while (flagNumber >= 0):
            pool = Pool(square, startMass)
            pool.add_new_biomass(amountFish, mass, 0, date.date.today())
            x = pool.calculate_difference_between_number_growth_days_and_limit_days(amountFish)
            flagNumber = x[0]
            if (flagNumber >= 0):
                amountFish += step
                amountGrowthDays = x[1]
                amountDaysBeforeLimit = x[2]

        return [amountFish, amountGrowthDays, amountDaysBeforeLimit]

    def calculate_max_average_mass(self, square, maxDensity, amountDays, startMass, step, amountFish, feedRatio, ):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllArrayFish.calculate_density_after_some_days

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_int, c_float]
        calculateLib.restype = c_float

        currentMass = startMass
        currentDensity = 0
        while(currentDensity < maxDensity):
            # созданим объект FishArray
            fishArray = FishArray()
            fishArray.add_biomass(date.date.today(), amountFish, currentMass)
            # соберем массивы масс и коэффициентов массонакопления
            arrayMass = assemble_array(fishArray.get_array_fish(), amountFish, 2)
            arrayMassAccumulationCoefficient = assemble_array(fishArray.get_array_fish(),
                                                              amountFish, 1)

            biomass = c_float(0.0)
            for i in range(amountFish):
                biomass.value += arrayMass[i] / 1000

            currentDensity = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                      amountFish, feedRatio,
                                      byref(biomass), amountDays,
                                      square)
            if (currentDensity < maxDensity):
                currentMass += step

        return currentMass


class CWSD():
    amountModules = 0
    modules = list()
    square = 0
    masses = 0
    salary = 0
    amountWorkers = 0
    equipmentCapacity = 0
    rent = 0
    costElectricity = 0
    deferredProcent = 0
    costCWSD = 0

    def __init__(self, amountModeles):
        self.amountModules = amountModeles
        self.modules = list()


masses = [100, 70, 50, 20]
cwsd = Module(20, masses, 30000, 2, 4, 4, 1000, 200, 5.5, 70000, 3.17, 21, 5, 0)

cwsd.main_work1(date.date.today(), date.date(2028, 1, 1), masses, 20)
cwsd.show_all_information_every_month(date.date.today(), date.date(2028, 1, 1))
for i in range(len(cwsd.budget)):
    print(cwsd.budget[i])