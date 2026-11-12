import csv
import json
import re
from collections import defaultdict, Counter

DATA_CSV = "data.csv"
OUTPUT_JSON = "data/stats.json"
MAX_ALLOWED_YEAR = 1936

OCCUPATION_STEMS = (
    'maker', 'makers', 'worker', 'workers', 'driver', 'drivers', 
    'vendor', 'dealers', 'keeper', 'smith', 'monger', 'fitter',
    'wright', 'man', 'men', 'repairer', 'machinist', 'operator'
)

COMMON_FORENAMES = {
    'john', 'mary', 'elizabeth', 'james', 'ann', 'anne', 'george', 'william', 
    'thomas', 'david', 'henry', 'sarah', 'jane', 'charles', 'margaret', 'robert', 
    'edward', 'arthur', 'richard', 'joseph', 'samuel', 'frederick', 'alfred', 
    'ellen', 'alice', 'hannah', 'emma', 'martha', 'florence', 'annie', 'edith', 
    'walter', 'albert', 'frank', 'herbert', 'ernest', 'harry', 'harold', 'percy', 
    'sidney', 'sydney', 'edgar', 'clarence', 'lewis', 'evans', 'davies', 'jones',
    'williams', 'rederick', 'lewellin', 'llewellyn', 'mrs', 'miss', 'widow',
    'wm', 'hy', 'jas', 'ed', 'edw', 'alf', 'geo', 'chas', 'thos', 'benj', 'saml', 'danl'
}

KNOWN_TRADES = {
    'labourer', 'ironworker', 'carpenter', 'mason', 'g.w.r', 'fitter', 'haulier', 
    'clerk', 'painter', 'grocer', 'seaman', 'engine driver', 'smith', 'tailor', 
    'butcher', 'trimmer', 'baker', 'engineer', 'plasterer', 'guard', 'moulder', 
    'gardener', 'foreman', 'boilermaker', 'fireman', 'builder', 'traveller', 
    'manager', 'hairdresser', 'coal trimmer', 'agent', 'blacksmith', 'greengrocer', 
    'bootmaker', 'signalman', 'shipwright', 'widow', 'plumber', 'hobbler', 
    'platelayer', 'porter', 'bricklayer', 'rigger', 'shopkeeper', 'mariner', 
    'shoemaker', 'draper', 'steelworker', 'pilot', 'confectioner', 'postman', 
    'driver', 'sawyer', 'policeman', 'printer', 'sailor', 'solicitor', 'crane driver', 
    'mechanic', 'machinist', 'steward', 'assistant', 'stoker', 'joiner', 'striker', 
    'miller', 'tobacconist', 'dealer', 'salesman', 'fruiterer', 'caretaker', 
    'inspector', 'decorator', 'warehouseman', 'saddler', 'shunter', 'boatman', 
    'factory', 'hoistman', 'milkman', 'insurance agent', 'cooper', 'dairyman', 
    'dock labourer', 'watchmaker', 'electrician', 'accountant', 'hawker', 
    'dressmaker', 'cabinetmaker', 'general shop', 'wheelwright', 'master mariner', 
    'docker', 'roller', 'furnaceman', 'chemist', 'engineman', 'motor driver', 
    'weighman', 'gasfitter', 'puddler', 'coal merchant', 'timekeeper', 'gasworker', 
    'newsagent', 'checker', 'sailmaker', 'coachman', 'compositor', 'stevedore', 
    'storekeeper', 'packer', 'outfitter', 'tinsmith', 'carman', 'surgeon', 
    'ostler', 'watchman', 'shearer', 'patternmaker', 'architect', 'horseshoer',
    'currier', 'upholsterer', 'optician', 'stationer', 'photographer', 'surveyor',
    'dentist', 'ironmonger', 'pawnbroker', 'auctioneer', 'milliner', 'fishmonger',
    'brewer', 'beer retailer', 'publican', 'innkeeper', 'waiter', 'baker & grocer',
    'commercial traveller', 'bus driver', 'lorry driver', 'motor mechanic',
    'cinematograph operator', 'typewriter', 'telegraphist', 'nurse', 'midwife'
}

def analyze_dataset():
    print(f"Reading {DATA_CSV}...")
    
    total_records = 0
    records_with_trade = 0
    years_counter = Counter()
    years_with_trade = Counter()
    streets_set = set()
    
    # 1. Trades in Names
    trades_in_forename = []
    trades_in_surname = []
    trades_in_names_by_year = Counter()
    detected_trade_counts = Counter()
    
    # 2. Names in Trades
    names_in_trades = []
    names_in_trades_by_year = Counter()
    detected_name_in_trade_counts = Counter()
    initials_in_trades_by_year = Counter()
    
    # 3. Overall Trades
    trade_counts = Counter()
    trades_by_year = defaultdict(Counter)
    trade_year_spans = defaultdict(lambda: {"earliest": 9999, "latest": 0, "count": 0})
    
    # 4. Streets & Trades
    street_trades = defaultdict(Counter)
    street_records = Counter()
    
    # 5. Women in directory
    women_records_by_year = Counter()
    women_trades = Counter()
    
    # 6. Specific Anomaly Categories
    anomaly_counts = {
        "ditto_variants": 0,
        "pure_symbols": 0,
        "single_initial_trade": 0,
        "numbers_in_trade": 0,
        "short_tokens": 0,
        "spillover_suffix": 0
    }
    anomaly_samples = defaultdict(list)
    
    # Build regexes
    trade_word_pattern = re.compile(
        r'\b(?:' + '|'.join(re.escape(t) for t in sorted(KNOWN_TRADES, key=len, reverse=True)) + r')\b',
        re.IGNORECASE
    )
    
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yr_str = r.get("year", "").strip()
            if not yr_str.isdigit():
                continue
            yr = int(yr_str)
            if yr > MAX_ALLOWED_YEAR:
                continue
            total_records += 1
            street = r.get("street", "").strip()
            hn = r.get("house_number", "").strip()
            bldg = r.get("building_name", "").strip()
            sn = r.get("surname", "").strip()
            fn = r.get("forename", "").strip()
            tr = r.get("trade", "").strip()
            if tr.lower() in ('nan', 'none', 'null'):
                tr = ''
            
            years_counter[yr_str] += 1
            if street:
                streets_set.add(street)
                street_records[street] += 1
                
            has_trade = bool(tr)
            if has_trade:
                records_with_trade += 1
                years_with_trade[yr_str] += 1
                trade_counts[tr] += 1
                trades_by_year[yr_str][tr] += 1
                
                span = trade_year_spans[tr]
                span["count"] += 1
                if yr < span["earliest"]: span["earliest"] = yr
                if yr > span["latest"]: span["latest"] = yr
                
                if street:
                    street_trades[street][tr] += 1
                    
            # Check for Women householders
            full_fn_lower = fn.lower()
            full_sn_lower = sn.lower()
            is_woman = False
            for w_title in ('mrs', 'miss', 'widow', 'mrs.', 'miss.', 'spinster'):
                if w_title in full_fn_lower.split() or w_title in full_sn_lower.split() or tr.lower() == 'widow':
                    is_woman = True
                    break
            if is_woman:
                women_records_by_year[yr_str] += 1
                if tr and tr.lower() != 'widow':
                    women_trades[tr] += 1
                    
            # --- Check 1: Trades in Names ---
            # Search forename first (common parsing bleed: "John [painter]")
            fn_matches = trade_word_pattern.findall(fn)
            # Avoid false positives like surname "Mason" or forename "George"
            if fn_matches:
                for match in fn_matches:
                    m_clean = match.title()
                    # Filter out benign initials or legitimate family surnames/forenames
                    if len(match) > 2 and match.lower() not in ('smith', 'cook', 'baker', 'taylor', 'carter', 'mason', 'porter', 'miller', 'cooper', 'carpenter', 'butcher', 'packer', 'hawker', 'seaman', 'foreman', 'gardener', 'gardner', 'turner', 'clark', 'clarke', 'driver', 'agent', 'guard'):
                        trades_in_forename.append({
                            "year": yr_str,
                            "street": street,
                            "house_number": hn,
                            "surname": sn,
                            "forename": fn,
                            "trade": tr,
                            "found": m_clean,
                            "field": "forename"
                        })
                        trades_in_names_by_year[yr_str] += 1
                        detected_trade_counts[m_clean] += 1
                        break
            else:
                # Also check surname for explicit occupation words that are not regular surnames
                # e.g., "Labourer", "Ironworker", "Engine Driver", "Boilermaker"
                sn_lower = sn.lower()
                for explicit_trade in ('labourer', 'ironworker', 'engine driver', 'boilermaker', 'blacksmith', 'greengrocer', 'coal trimmer', 'shipwright', 'platelayer', 'hairdresser', 'shoemaker', 'railway guard', 'postman', 'tobacconist', 'plasterer', 'furnaceman'):
                    if explicit_trade in sn_lower:
                        trades_in_surname.append({
                            "year": yr_str,
                            "street": street,
                            "house_number": hn,
                            "surname": sn,
                            "forename": fn,
                            "trade": tr,
                            "found": explicit_trade.title(),
                            "field": "surname"
                        })
                        trades_in_names_by_year[yr_str] += 1
                        detected_trade_counts[explicit_trade.title()] += 1
                        break

            # --- Check 2: Names in Trades ---
            if tr:
                tr_lower = tr.strip('. ,').lower()
                tr_words = [w.strip('.,') for w in tr_lower.split()]
                
                # A. Single or 2-letter Initial as Trade (e.g. "J", "H", "Wm", "Hy")
                if len(tr) <= 3 and tr.isalpha() and tr.lower() not in ('etc', 'nan', 'bar', 'inn', 'pub', 'gwr'):
                    anomaly_counts["single_initial_trade"] += 1
                    initials_in_trades_by_year[yr_str] += 1
                    names_in_trades_by_year[yr_str] += 1
                    detected_name_in_trade_counts[tr.upper()] += 1
                    if len(anomaly_samples["initial_as_trade"]) < 25:
                        anomaly_samples["initial_as_trade"].append({
                            "year": yr_str, "street": street, "house_number": hn,
                            "surname": sn, "forename": fn, "trade": tr
                        })
                # B. Standalone Forenames as Trade (e.g. "John", "Mary", "Elizabeth", "George", "James")
                elif tr_lower in COMMON_FORENAMES and tr_lower not in ('widow',):
                    names_in_trades.append({
                        "year": yr_str,
                        "street": street,
                        "house_number": hn,
                        "surname": sn,
                        "forename": fn,
                        "trade": tr
                    })
                    names_in_trades_by_year[yr_str] += 1
                    detected_name_in_trade_counts[tr.title()] += 1
                
                # Check 3: Other specific OCR/trade anomaly types
                if tr_lower in ('do', 'do.', 'ditto', '"'):
                    anomaly_counts["ditto_variants"] += 1
                    if len(anomaly_samples["ditto_variants"]) < 20:
                        anomaly_samples["ditto_variants"].append({"year": yr_str, "street": street, "house_number": hn, "surname": sn, "forename": fn, "trade": tr})
                elif re.match(r'^[\s\*\-\_\=\#\+\|\.\:\/]+$', tr):
                    anomaly_counts["pure_symbols"] += 1
                    if len(anomaly_samples["pure_symbols"]) < 20:
                        anomaly_samples["pure_symbols"].append({"year": yr_str, "street": street, "house_number": hn, "surname": sn, "forename": fn, "trade": tr})
                elif re.match(r'^\d+$', tr):
                    anomaly_counts["numbers_in_trade"] += 1
                    if len(anomaly_samples["numbers_in_trade"]) < 20:
                        anomaly_samples["numbers_in_trade"].append({"year": yr_str, "street": street, "house_number": hn, "surname": sn, "forename": fn, "trade": tr})
                elif tr_lower in ('ltd', 'nan', 'etc', 'co'):
                    anomaly_counts["spillover_suffix"] += 1
                    if len(anomaly_samples["spillover_suffix"]) < 20:
                        anomaly_samples["spillover_suffix"].append({"year": yr_str, "street": street, "house_number": hn, "surname": sn, "forename": fn, "trade": tr})

    # Prepare structured summary payload
    sorted_years = sorted(years_counter.keys(), key=lambda y: int(y))
    
    # Top 50 Overall Trades
    top_trades_list = []
    for t, count in trade_counts.most_common(60):
        span = trade_year_spans[t]
        top_trades_list.append({
            "trade": t,
            "count": count,
            "earliest": span["earliest"],
            "latest": span["latest"]
        })
        
    # Decade evolution for top key trades
    decades = ["1870s", "1880s", "1890s", "1900s", "1910s", "1920s", "1930s"]
    decade_mapping = {
        "1876": "1870s", "1878": "1870s",
        "1882": "1880s", "1886": "1880s", "1887": "1880s",
        "1890": "1890s", "1892": "1890s", "1893": "1890s", "1894": "1890s", "1895": "1890s", "1898": "1890s", "1899": "1890s",
        "1900": "1900s", "1901": "1900s", "1902": "1900s", "1903": "1900s",
        "1910": "1910s", "1913": "1910s", "1915": "1910s",
        "1920": "1920s", "1924": "1920s", "1925": "1920s", "1927": "1920s",
        "1936": "1930s"
    }
    
    key_tracked_trades = [
        "Labourer", "Ironworker", "Steelworker", "Puddler", "Coal Trimmer", 
        "Seaman", "Carpenter", "Mason", "G.W.R", "Engine Driver", "Fitter", 
        "Haulier", "Clerk", "Painter", "Grocer", "Tailor", "Butcher", 
        "Baker", "Motor Driver", "Electrician"
    ]
    
    decade_trends = {t: {d: 0 for d in decades} for t in key_tracked_trades}
    for yr, t_dict in trades_by_year.items():
        dec = decade_mapping.get(yr)
        if not dec: continue
        for t in key_tracked_trades:
            decade_trends[t][dec] += t_dict.get(t, 0)
            
    # Street economic character
    top_commercial_streets = []
    top_industrial_streets = []
    top_railway_streets = []
    top_maritime_streets = []
    top_professional_streets = []
    
    for street, t_counter in street_trades.items():
        if street_records[street] < 50:
            continue
        total_st_trades = sum(t_counter.values())
        if total_st_trades == 0:
            continue
            
        comm_score = sum(t_counter[t] for t in ('Grocer', 'Draper', 'Butcher', 'Baker', 'Confectioner', 'Tobacconist', 'Chemist', 'Tailor', 'Bootmaker', 'Outfitter'))
        ind_score = sum(t_counter[t] for t in ('Ironworker', 'Labourer', 'Puddler', 'Moulder', 'Boilermaker', 'Striker', 'Smith', 'Roller', 'Furnaceman', 'Steelworker'))
        rail_score = sum(t_counter[t] for t in ('G.W.R', 'Engine Driver', 'Guard', 'Signalman', 'Platelayer', 'Shunter', 'Railway Guard'))
        mar_score = sum(t_counter[t] for t in ('Seaman', 'Coal Trimmer', 'Trimmer', 'Rigger', 'Shipwright', 'Pilot', 'Stevedore', 'Docker', 'Hobbler', 'Boatman', 'Sailmaker'))
        prof_score = sum(t_counter[t] for t in ('Solicitor', 'Accountant', 'Surgeon', 'Architect', 'Dentist', 'Surveyor'))
        
        if comm_score >= 15:
            top_commercial_streets.append({"street": street, "count": comm_score, "total": total_st_trades, "pct": round(comm_score/total_st_trades*100, 1)})
        if ind_score >= 20:
            top_industrial_streets.append({"street": street, "count": ind_score, "total": total_st_trades, "pct": round(ind_score/total_st_trades*100, 1)})
        if rail_score >= 15:
            top_railway_streets.append({"street": street, "count": rail_score, "total": total_st_trades, "pct": round(rail_score/total_st_trades*100, 1)})
        if mar_score >= 15:
            top_maritime_streets.append({"street": street, "count": mar_score, "total": total_st_trades, "pct": round(mar_score/total_st_trades*100, 1)})
        if prof_score >= 5:
            top_professional_streets.append({"street": street, "count": prof_score, "total": total_st_trades, "pct": round(prof_score/total_st_trades*100, 1)})
            
    top_commercial_streets.sort(key=lambda x: x["count"], reverse=True)
    top_industrial_streets.sort(key=lambda x: x["count"], reverse=True)
    top_railway_streets.sort(key=lambda x: x["count"], reverse=True)
    top_maritime_streets.sort(key=lambda x: x["count"], reverse=True)
    top_professional_streets.sort(key=lambda x: x["count"], reverse=True)

    # Vanished vs Emerging Trades
    vanished_trades = []
    emerging_trades = []
    for t, span in trade_year_spans.items():
        if span["count"] >= 30 and span["earliest"] <= 1895 and span["latest"] <= 1920:
            vanished_trades.append({"trade": t, "count": span["count"], "earliest": span["earliest"], "latest": span["latest"]})
        elif span["count"] >= 30 and span["earliest"] >= 1915:
            emerging_trades.append({"trade": t, "count": span["count"], "earliest": span["earliest"], "latest": span["latest"]})
            
    vanished_trades.sort(key=lambda x: x["count"], reverse=True)
    emerging_trades.sort(key=lambda x: x["count"], reverse=True)

    stats_output = {
        "meta": {
            "total_records": total_records,
            "total_with_trade": records_with_trade,
            "pct_with_trade": round(records_with_trade / total_records * 100, 1),
            "total_streets": len(streets_set),
            "total_years": len(sorted_years),
            "years_span": f"{sorted_years[0]}–{sorted_years[-1]}",
            "unique_trade_strings": len(trade_counts)
        },
        "yearly_overview": [
            {
                "year": y,
                "total": years_counter[y],
                "with_trade": years_with_trade[y],
                "pct": round(years_with_trade[y] / years_counter[y] * 100, 1) if years_counter[y] else 0,
                "trades_in_names": trades_in_names_by_year[y],
                "names_in_trades": names_in_trades_by_year[y]
            }
            for y in sorted_years
        ],
        "trades_in_names": {
            "total_detected": len(trades_in_forename) + len(trades_in_surname),
            "in_forename_count": len(trades_in_forename),
            "in_surname_count": len(trades_in_surname),
            "top_trapped_trades": [{"trade": t, "count": c} for t, c in detected_trade_counts.most_common(30)],
            "by_year": {y: trades_in_names_by_year[y] for y in sorted_years if trades_in_names_by_year[y] > 0},
            "samples": (trades_in_forename[:35] + trades_in_surname[:15])
        },
        "names_in_trades": {
            "total_detected": len(names_in_trades) + anomaly_counts["single_initial_trade"],
            "initials_as_trade_count": anomaly_counts["single_initial_trade"],
            "forenames_as_trade_count": len(names_in_trades),
            "top_names": [{"name": n, "count": c} for n, c in detected_name_in_trade_counts.most_common(30)],
            "by_year": {y: names_in_trades_by_year[y] for y in sorted_years if names_in_trades_by_year[y] > 0},
            "samples": (anomaly_samples["initial_as_trade"][:25] + names_in_trades[:25])
        },
        "top_trades": top_trades_list,
        "decade_trends": decade_trends,
        "decades": decades,
        "tracked_trades": key_tracked_trades,
        "street_specialization": {
            "commercial": top_commercial_streets[:15],
            "industrial": top_industrial_streets[:15],
            "railway": top_railway_streets[:15],
            "maritime": top_maritime_streets[:15],
            "professional": top_professional_streets[:15]
        },
        "women_in_directories": {
            "total_female_heads": sum(women_records_by_year.values()),
            "by_year": {y: women_records_by_year[y] for y in sorted_years},
            "top_trades": [{"trade": t, "count": c} for t, c in women_trades.most_common(25)]
        },
        "vanished_trades": vanished_trades[:25],
        "emerging_trades": emerging_trades[:25],
        "anomalies": {
            "counts": anomaly_counts,
            "samples": anomaly_samples
        }
    }
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f_out:
        json.dump(stats_output, f_out, indent=2)
        
    print(f"Generated {OUTPUT_JSON} successfully!")
    print(f"Total records analyzed: {total_records:,}")
    print(f"Trades in names detected: {len(trades_in_forename) + len(trades_in_surname):,}")
    print(f"Names in trades detected: {len(names_in_trades) + anomaly_counts['single_initial_trade']:,}")

if __name__ == "__main__":
    analyze_dataset()
