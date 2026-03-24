from src.sandhi_simple import Sandhi
from src.transliterate import transliterate_text
from src.bandha import Bandha

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def hamming(s1, s2):
    if len(s1) != len(s2):
        return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def search_grid(chakra, target, measure='exact', max_distance=0, script='kannada', use_sandhi=False):
    """
    Unified search that works for both Devanagari and Kannada scripts.
    
    Strategy:
    1. Transliterate target to Devanagari for processing
    2. Extract grid text in Devanagari
    3. Apply Devanagari Sandhi conversion if enabled
    4. Match using Devanagari strings
    5. Transliterate results back to target script for display
    
    Returns a list of match dictionaries sorted by distance.
    """
    results = []
    rows, cols = 27, 27
    
    if not target:
        return results
    
    # Step 1: Transliterate target to Devanagari for processing
    if script == 'kannada':
        target_devanagari = transliterate_text(target, 'devanagari')
    else:
        target_devanagari = target
    
    # Apply Sandhi to target if enabled
    target_processed = Sandhi(target_devanagari) if use_sandhi else target_devanagari
    
    target_len = len(target_processed)
    
    directions = [
        (0, 1),   # Right
        (1, 0),   # Down
        (0, -1),  # Left
        (-1, 0),  # Up
        (1, 1),   # Down-Right
        (1, -1),  # Down-Left
        (-1, 1),  # Up-Right
        (-1, -1)  # Up-Left
    ]
    
    for r in range(rows):
        for c in range(cols):
            for dr, dc in directions:
                # Determine search length based on target
                if measure == 'exact':
                    cells_to_extract = target_len
                else:
                    # For fuzzy matching, allow some flexibility
                    cells_to_extract = min(target_len + max_distance, 27)
                
                path = []
                curr_r, curr_c = r, c
                
                for _ in range(cells_to_extract):
                    if 0 <= curr_r < rows and 0 <= curr_c < cols:
                        path.append([curr_r, curr_c])
                    else:
                        break
                    
                    curr_r += dr
                    curr_c += dc
                
                # Try different path lengths for fuzzy matching
                min_len = target_len if measure == 'exact' else max(1, target_len - max_distance)
                max_len = target_len if measure == 'exact' else min(len(path), target_len + max_distance)
                
                for path_len in range(min_len, max_len + 1):
                    test_path = path[:path_len]
                    
                    # Extract text in both scripts
                    test_text_dev = ""
                    test_text_display = ""
                    valid_path = True
                    
                    for pr, pc in test_path:
                        akshara_res = chakra.get_akshara_at(pr, pc, script)
                        if not akshara_res or akshara_res[0] == "?":
                            valid_path = False
                            break
                        
                        # Get Devanagari for processing
                        test_text_dev += akshara_res[1]
                        # Keep original script for display
                        test_text_display += akshara_res[0] if script == 'kannada' else akshara_res[1]
                    
                    if not valid_path or not test_text_dev:
                        continue
                    
                    # Apply Sandhi conversion in Devanagari
                    test_processed = Sandhi(test_text_dev) if use_sandhi else test_text_dev
                    
                    # Calculate distance based on measure
                    if measure == 'exact':
                        if test_processed == target_processed:
                            distance = 0
                        else:
                            continue
                    elif measure == 'hamming':
                        if len(test_processed) == len(target_processed):
                            distance = hamming(test_processed, target_processed)
                        else:
                            continue
                    elif measure == 'levenshtein':
                        distance = levenshtein(test_processed, target_processed)
                    else:
                        continue
                    
                    if distance <= max_distance:
                        # Transliterate processed Devanagari back to target script for display
                        if script == 'kannada':
                            processed_display = transliterate_text(test_processed, 'kannada')
                        else:
                            processed_display = test_processed
                        
                        # Only add Sandhi converted text if it's different from extracted
                        sandhi_converted = processed_display if use_sandhi and processed_display != test_text_display else None
                        
                        results.append({
                            'path': test_path,
                            'extracted_text': test_text_display,
                            'sandhi_converted_text': sandhi_converted,
                            'distance': distance,
                            'measure': measure
                        })
                        
                        # For exact matches, we can break early
                        if measure == 'exact' and distance == 0:
                            break
                
                # Break early for exact matches
                if measure == 'exact' and results and results[-1]['distance'] == 0:
                    break
    
    # Sort results by distance and path length
    results.sort(key=lambda x: (x['distance'], len(x['path'])))
    
    # Deduplicate paths
    unique_results = []
    seen = set()
    for res in results:
        path_tuple = tuple(tuple(p) for p in res['path'])
        if path_tuple not in seen:
            seen.add(path_tuple)
            unique_results.append(res)
            
    return unique_results

def search_with_bandha_patterns(chakra, target, pattern_type, pattern_params, measure='exact', max_distance=0, script='kannada', use_sandhi=False):
    """
    Search using specific Bandha path patterns.
    
    Args:
        chakra: The Chakra object to search in
        target: Target text to search for
        pattern_type: Type of pattern ('horizontal_zigzag', 'vertical_zigzag', 'chess_knight')
        pattern_params: Parameters for the pattern:
            - For zigzag: {'start_row': int, 'start_col': int, 'length': int}
            - For chess_knight: {'start_row': int, 'start_col': int, 'num_jumps': int, 'constraints': dict}
        measure: Distance measure ('exact', 'hamming', 'levenshtein')
        max_distance: Maximum allowed distance for fuzzy matching
        script: Script to use ('kannada' or 'devanagari')
        use_sandhi: Whether to apply Sandhi conversion
    
    Returns:
        List of match dictionaries
    """
    results = []
    
    if not target:
        return results

    # Create Bandha instance and generate path
    bandha = Bandha()
    
    try:
        if pattern_type == 'horizontal_zigzag':
            path = bandha.horizontal_zigzag(
                pattern_params['start_row'],
                pattern_params['start_col'],
                pattern_params['length']
            )
        elif pattern_type == 'vertical_zigzag':
            path = bandha.vertical_zigzag(
                pattern_params['start_row'],
                pattern_params['start_col'],
                pattern_params['length']
            )
        elif pattern_type == 'chess_knight':
            path = bandha.chess_knight_moves(
                pattern_params['start_row'],
                pattern_params['start_col'],
                pattern_params['num_jumps'],
                pattern_params.get('constraints')
            )
        elif pattern_type == 'shreni_bandha':
            path = bandha.shreni_bandha(
                pattern_params['start_row'],
                pattern_params['start_col'],
                pattern_params['num_steps'],
                pattern_params.get('direction', 'up')
            )
            # print(f'params {pattern_params} path {path}')
        else:
            return results
        
        # Extract text along the path
        extracted_text_dev = ""
        extracted_text_display = ""
        valid_path = True
        
        for pr, pc in path:
            akshara_res = chakra.get_akshara_at(pr, pc, script)
            if not akshara_res or akshara_res[0] == "?":
                valid_path = False
                break
            
            # Get Devanagari for processing
            extracted_text_dev += akshara_res[1]
            # Keep original script for display
            extracted_text_display += akshara_res[0] if script == 'kannada' else akshara_res[1]
        # print(f'res 1 {results}')
        if not valid_path or not extracted_text_dev:
            # print(f'res not valid path {results}')
            return results
        
        # Process target text
        if script == 'kannada':
            target_devanagari = transliterate_text(target, 'devanagari')
        else:
            target_devanagari = target
        
        target_processed = Sandhi(target_devanagari) if use_sandhi else target_devanagari
        target_len = len(target_processed)
        
        # Try different path lengths for fuzzy matching (like standard search)
        min_len = target_len if measure == 'exact' else max(1, target_len - max_distance)
        max_len = target_len if measure == 'exact' else max(len(path), target_len + max_distance)
        # print(f'path len {len(path)} other {target_len + max_distance} max {max_len} min {min_len}')
        # print(f'res 3 {results}')
        for path_len in range(min_len, max_len + 1):
            # Take only the first path_len characters
            test_text_dev = extracted_text_dev[:path_len]
            test_text_display = extracted_text_display[:path_len]

            # Apply Sandhi to extracted text if enabled
            test_processed = Sandhi(test_text_dev) if use_sandhi else test_text_dev
            # print(f'target_processed {target_processed} {target_len} test_processed {test_processed} {len(test_processed)} test_text dev {test_text_dev} {len(test_text_dev)} display {test_text_display} {len(test_text_display)}')

            # Calculate distance based on measure
            if measure == 'exact':
                if test_processed == target_processed:
                    distance = 0
                else:
                    continue
            elif measure == 'hamming':
                # For hamming distance, allow different lengths by comparing substrings
                if len(test_processed) >= len(target_processed):
                    # Compare first target_len characters
                    test_substring = test_processed[:len(target_processed)]
                    distance = hamming(test_substring, target_processed)
                elif len(test_processed) <= len(target_processed):
                    # Compare entire test_processed with first test_len characters of target
                    target_substring = target_processed[:len(test_processed)]
                    distance = hamming(test_processed, target_substring)
                else:
                    continue
            elif measure == 'levenshtein':
                distance = levenshtein(test_processed, target_processed)
            else:
                continue
            # print(f'res 4 {results}')
            if distance <= max_distance:
                # Transliterate processed Devanagari back to target script for display
                if script == 'kannada':
                    processed_display = transliterate_text(test_processed, 'kannada')
                else:
                    processed_display = test_processed
                # print(f'processed_display 5 {processed_display}')
                # Only add Sandhi converted text if it's different from extracted
                sandhi_converted = processed_display if use_sandhi and processed_display != test_text_display else None
                # print(f'sandhi_converted 5 {sandhi_converted}')
                results = []
                results.append({
                    'path': path[:path_len],  # Use the truncated path
                    'extracted_text': test_text_display,
                    'sandhi_converted_text': sandhi_converted,
                    'distance': distance,
                    'measure': measure,
                    'pattern_type': pattern_type,
                    'pattern_params': pattern_params
                })
                
                # For exact matches, we can break early
                if measure == 'exact' and distance == 0:
                    break
    
    except Exception as e:
        print(f"Error in pattern search: {e}")
        return results
    
    return results

def search_all_pattern_variants(chakra, target, pattern_type, measure='exact', max_distance=0, script='kannada', use_sandhi=False):
    """
    Search using all possible starting positions and parameters for a given pattern type.
    
    Args:
        chakra: The Chakra object to search in
        target: Target text to search for
        pattern_type: Type of pattern ('horizontal_zigzag', 'vertical_zigzag', 'chess_knight')
        measure: Distance measure ('exact', 'hamming', 'levenshtein')
        max_distance: Maximum allowed distance for fuzzy matching
        script: Script to use ('kannada' or 'devanagari')
        use_sandhi: Whether to apply Sandhi conversion
    
    Returns:
        List of match dictionaries
    """
    all_results = []
    target_len = len(target)
    
    if pattern_type in ['horizontal_zigzag', 'vertical_zigzag']:
        # Try all starting positions
        for start_row in range(27):
            for start_col in range(27):
                pattern_params = {
                    'start_row': start_row,
                    'start_col': start_col,
                    'length': target_len
                }
                
                results = search_with_bandha_patterns(
                    chakra, target, pattern_type, pattern_params,
                    measure, max_distance, script, use_sandhi
                )
                all_results.extend(results)
    
    elif pattern_type == 'chess_knight':
        # For knight moves, try different numbers of jumps
        for num_jumps in range(target_len - 1, target_len + 2):  # Try nearby lengths
            for start_row in range(27):
                for start_col in range(27):
                    pattern_params = {
                        'start_row': start_row,
                        'start_col': start_col,
                        'num_jumps': num_jumps,
                        'constraints': None
                    }
                    
                    results = search_with_bandha_patterns(
                        chakra, target, pattern_type, pattern_params,
                        measure, max_distance, script, use_sandhi
                    )
                    all_results.extend(results)
    
    elif pattern_type == 'shreni_bandha':
        # For Shreni Bandha, try both directions and all starting positions
        # Generate longer paths to allow different length matching
        for direction in ['up', 'down']:
            for start_row in range(27):
                for start_col in range(27):
                    # Generate a longer path to allow different length matching
                    max_path_length = min(len(target) + max_distance + 3, 27)  # Add some extra length
                    pattern_params = {
                        'start_row': start_row,
                        'start_col': start_col,
                        'num_steps': max_path_length,
                        'direction': direction
                    }
                    
                    results = search_with_bandha_patterns(
                        chakra, target, pattern_type, pattern_params,
                        measure, max_distance, script, use_sandhi
                    )
                    all_results.extend(results)
    
    # Sort results by distance, path length, and then by position (top-left preference)
    all_results.sort(key=lambda x: (x['distance'], len(x['path']),
                                      x['pattern_params']['start_row'],
                                      x['pattern_params']['start_col']))
    
    return all_results
