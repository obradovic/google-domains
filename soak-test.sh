#!/bin/bash

for i in {1..200}; do
    echo
    echo "ITERATION $i"
    TIMEFORMAT="That add took %1R seconds" time google-domains -q add foo google.com
    TIMEFORMAT="That del took %1R seconds" time google-domains -q del foo
done

