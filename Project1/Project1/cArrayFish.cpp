#include <stdio.h>
#include <math.h>


extern "C" __declspec(dllexport) float update_biomass(
	float* fishArray,
	int amountFish
)
{
	float biomass = 0.0;

	for (int i = 0; i < amountFish; i++) {
		biomass += fishArray[i];
	}

	biomass = biomass / 1000;
	return biomass;
}


extern "C" __declspec(dllexport) float _calculation_daily_growth(
	float previousMass,
	float massAccumulationCoefficient,
	float* biomass
)
{
	float y = 1.0 / 3.0;
	float x = powf(previousMass, y);
	float newMass = x + (massAccumulationCoefficient / 3);
	newMass = powf(newMass, 3);
	*biomass += (newMass - previousMass) / 1000;
	return newMass;
}


extern "C" __declspec(dllexport) float _determination_total_daily_weight_feed(
	float previousMass,
	float currentMass,
	float feedRatio
)
{
	float relativeGrowth = (float(currentMass) - float(previousMass))
		/ float(previousMass);
	float result = previousMass * relativeGrowth * feedRatio;
	return result;
}


extern "C" __declspec(dllexport) float daily_work(
	float* arrayMass,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass
)
{
	// ���������� ����� �����
	float dailyFeedMass = 0.0;
	float previousMass = 0.0;

	for (int i = 0; i < amountFish; i++) {
		previousMass = arrayMass[i];
		// �������� ����� �����
		arrayMass[i] = _calculation_daily_growth(
			arrayMass[i],
			arrayMassAccumulationCoefficient[i],
			biomass);
		// ����������� ����� ����� �� ����������� ����
		dailyFeedMass += _determination_total_daily_weight_feed(
			previousMass,
			arrayMass[i],
			feedRatio
		);
	}

	dailyFeedMass = dailyFeedMass / 1000;
	return dailyFeedMass;
}


extern "C" __declspec(dllexport) float do_daily_work_some_days
(
	float* arrayMass,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass,
	int amountDays
)
{
	float totalFeedMass = 0.0;
	for (int i = 0; i < amountDays; i++) {
		totalFeedMass += daily_work(arrayMass, arrayMassAccumulationCoefficient,
			amountFish, feedRatio, biomass);

	}
	return totalFeedMass;
}


extern "C" __declspec(dllexport) int calculate_when_fish_will_be_sold
(
	float* arrayMass,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass,
	float massComercialFish,
	int packageValue
)
{
	int amountDays = 0;
	int amountSoldFish = 0;

	// ����� ������ ���������� ������, ���� �� ������� ����������� �������� ���� ��� ��� ����
	while ((amountSoldFish < packageValue) && (amountSoldFish != amountFish))
	{
		daily_work(arrayMass, arrayMassAccumulationCoefficient,
			amountFish, feedRatio, biomass);
		// ���������, ������� �� ���������� ����
		amountSoldFish = 0;
		for (int i = 0; i < amountFish; i++)
		{
			if (arrayMass[i] >= massComercialFish) amountSoldFish++;
		}
		// ���������� ����
		amountDays++;
	}
	// ���������� ���������� ����, ����������� ��� ����������� ������ ����
	return amountDays;
}


extern "C" __declspec(dllexport) int calculate_when_density_reaches_limit
(
	float* arrayMass,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass,
	float maxDensity,
	float square
)
{
	int amountDays = 0;
	float currentDensity = *biomass / square;

	while (currentDensity < maxDensity)
	{
		daily_work(arrayMass, arrayMassAccumulationCoefficient,
			amountFish, feedRatio, biomass);
		currentDensity = *biomass / square;
		amountDays++;
	}
	return amountDays;
}


extern "C" __declspec(dllexport) int calculate_how_many_fish_needs
(
	float* arrayMass1,
	float* arrayMass2,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass1,
	float* biomass2,
	float massComercialFish,
	int packageValue,
	float maxDensity,
	float square,
	int* resultAmountsDays

)
{
	int amountDayWhenFishGrowUp = calculate_when_fish_will_be_sold(arrayMass1, arrayMassAccumulationCoefficient,
		amountFish, feedRatio, biomass1, massComercialFish, packageValue);
	int amountDayWhenFishReachLimit = calculate_when_density_reaches_limit(arrayMass2, arrayMassAccumulationCoefficient,
		amountFish, feedRatio, biomass2, maxDensity, square);
	int result = amountDayWhenFishReachLimit - amountDayWhenFishGrowUp;
	resultAmountsDays[0] = amountDayWhenFishGrowUp;
	resultAmountsDays[1] = amountDayWhenFishReachLimit;
	return result;
}

extern "C" __declspec(dllexport) float calculate_density_after_some_days
(
	float* arrayMass,
	float* arrayMassAccumulationCoefficient,
	int amountFish,
	float feedRatio,
	float* biomass,
	int amountDays,
	float square
)
{
	do_daily_work_some_days(arrayMass, arrayMassAccumulationCoefficient, amountFish, feedRatio, biomass, amountDays);
	float resultDensity = *biomass / square;
	return resultDensity;
}