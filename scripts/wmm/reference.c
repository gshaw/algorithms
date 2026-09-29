/*
 * Runs NOAA's own WMM2025 library over reference-input.txt, for the cases NOAA's
 * published tables don't cover. Built against NOAA's source by generate.sh.
 *
 * Input, one per line:
 *   field <latitude> <longitude> <height km> <decimal year>
 *   date <year> <month> <day>
 */
#include <stdio.h>
#include <string.h>

#include "GeomagnetismHeader.h"
#include "EGM9615.h"
#include "magcalc.h"

int main(void)
{
    MAGtype_MagneticModel *MagneticModels[1], *TimedMagneticModel;
    MAGtype_Ellipsoid Ellip;
    MAGtype_Geoid Geoid;
    char line[256], kind[16];

    if (!MAG_robustReadMagModels("WMM.COF", &MagneticModels, 1)) return 1;
    TimedMagneticModel = allocate_coefsArr_memory(0, MagneticModels[0]);
    MAG_SetDefaults(&Ellip, &Geoid);
    Geoid.GeoidHeightBuffer = GeoidHeightBuffer;
    Geoid.Geoid_Initialized = 1;

    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, "%15s", kind) != 1 || kind[0] == '#') continue;
        if (strcmp(kind, "field") == 0) {
            MAGtype_CoordGeodetic g = {0};
            MAGtype_CoordSpherical s;
            MAGtype_Date d = {0};
            MAGtype_GeoMagneticElements e, err;
            sscanf(line, "%*s %lf %lf %lf %lf", &g.phi, &g.lambda, &g.HeightAboveEllipsoid, &d.DecimalYear);
            MAG_GeodeticToSpherical(Ellip, g, &s);
            point_calc(Ellip, g, &s, d, MagneticModels[0], TimedMagneticModel, &e, &err);
            printf("field %.6f %.6f %.6f %.6f D %.6f I %.6f X %.6f Y %.6f Z %.6f H %.6f F %.6f GV %.6f\n",
                   g.phi, g.lambda, g.HeightAboveEllipsoid, d.DecimalYear,
                   e.Decl, e.Incl, e.X, e.Y, e.Z, e.H, e.F, e.GV);
        } else if (strcmp(kind, "date") == 0) {
            MAGtype_Date d = {0};
            char error[255] = "";
            sscanf(line, "%*s %d %d %d", &d.Year, &d.Month, &d.Day);
            if (MAG_DateToYear(&d, error))
                printf("date %04d-%02d-%02d %.10f\n", d.Year, d.Month, d.Day, d.DecimalYear);
            else
                printf("date %04d-%02d-%02d invalid\n", d.Year, d.Month, d.Day);
        }
    }
    return 0;
}
