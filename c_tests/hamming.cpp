#include <iostream>
#include <string>

// display array of bools as blocks 4x4 blocks
void print_44_blocks(bool* data, int len) {
    for (int block = 0; block<len; block+=16) {
        for (int row = 0; row<4; row++) {
            for (int val = 0; val<4; val++) {
                std::cout << *(data+val + (row*4) + block) << " ";
            }
            std::cout << "\n";
        }
        std:: cout << "\n";
    }
}

int encode_hamming_11(bool *arr, int len, bool *out) {
    // calculate minimum required 4x4 blocks
    // and the length of the output stream
    int num_blocks = len/11 + (int)(len%11 != 0);
    int out_len = num_blocks * 16;

    bool *curr = arr; //pointer to curr val in arr
    *out = new bool[out_len]; //re-init out to the correct size
    for (int block = 0; block < num_blocks; block++) {
        int offset = 16*block;

        // parity bit counters
        int odd_col = 0;
        int right_col = 0;
        int odd_row = 0;
        int bot_row = 0;
        int toal_parity = 0;


        for (int i = 0; i<16; i++) {
            //data bit as long as its not in a parity bit location (log_2(x) is int)
            bool isData = !(i == 0 || i == 1 || i == 2 || i == 4 || i == 8);
            bool val = (len>0) ? *curr : 0; //default to 0 if no bits are left

            if (isData) {
                // count parity bits
                if (i%2 != 0) {
                    odd_col += val;
                }
                if ((i - ((i/4)*4)) >= 2) {
                    right_col += val;
                }
                if ((i >= 4 && i <= 7) || (i >= 12 && i <= 15)) {
                    odd_row += val;
                }
                if (i >= 8) {
                    bot_row += val;
                }
                toal_parity += val;

                // set and adjust value
                out[offset + i] = val;
                
                if (len>0) {
                    curr += 1;
                    len -= 1;
                }
            }
        }

        // set parity bits in array
        out[offset + 1] = (odd_col % 2 != 0);
        out[offset + 2] = (right_col % 2 != 0);
        out[offset + 4] = (odd_row % 2 != 0);
        out[offset + 8] = (bot_row % 2 != 0);

        // calculate and set value for total parity bit
        toal_parity += out[offset + 1] + out[offset + 2] + out[offset + 4] + out[offset + 8];
        out[offset] = (toal_parity % 2 != 0);

        

    }
    
    return out_len;
}


int decode_hamming_11(bool *encoded, int len, bool *out, bool* hasDoubleFlip, int *numErrors) {
    int num_blocks = len/16;
    int out_len = num_blocks * 11;

    *numErrors = 0;
    *hasDoubleFlip = false;

    *out = new bool[out_len];
    int out_pos = 0;
    for (int block=0; block<num_blocks; block++) {
        int offset = block*11;
        int block_offset = block*16;

        int odd_col = 0;
        int right_col = 0;
        int odd_row = 0;
        int bot_row = 0;
        int total_parity = 0;

        for (int i = 0; i<16; i++) {
            //data bit as long as its not in a parity bit location (log_2(x) is int)
            bool isData = !(i == 0 || i == 1 || i == 2 || i == 4 || i == 8);
            bool val = encoded[block_offset+i];

            if (isData) {
                // count parity bits
                if (i%2 != 0) {
                    odd_col += val;
                }
                if ((i - ((i/4)*4)) >= 2) {
                    right_col += val;
                }
                if ((i >= 4 && i <= 7) || (i >= 12 && i <= 15)) {
                    odd_row += val;
                }
                if (i >= 8) {
                    bot_row += val;
                }
                total_parity += val;

                // set and adjust value
                out[out_pos] = val;
                out_pos += 1;
            }
        }
    
        bool error_odd_col = encoded[block_offset + 1] != (odd_col % 2 != 0);
        bool error_rgt_col = encoded[block_offset + 2] != (right_col % 2 != 0);
        bool error_odd_row = encoded[block_offset + 4] != (odd_row % 2 != 0);
        bool error_bot_row = encoded[block_offset + 8] != (bot_row % 2 != 0);

        // calculate and set value for total parity bit
        total_parity += encoded[block_offset + 1] + encoded[block_offset + 2] + encoded[block_offset + 4] + encoded[block_offset + 8];
        bool error_total = encoded[block_offset] != (total_parity % 2 != 0);

        int error_col = 0;
        if (error_odd_col) {
            if (error_rgt_col)
                error_col = 3;
            else
                error_col = 1;
        }
        else if (error_rgt_col)
            error_col = 2;

        int error_row = 0;
        if (error_odd_row) {
            if (error_bot_row)
                error_row = 3;
            else
                error_row = 1;
        }
        else if (error_bot_row)
            error_row = 2;

        if (error_odd_col || error_rgt_col || error_odd_row || error_bot_row) {
            if (!error_total) {
                *hasDoubleFlip = true;
            }
            else {
                int pos = (error_row*4) + error_col;
                bool isData = !(pos == 0 || pos == 1 || pos == 2 || pos == 4 || pos == 8);
                
                if (!(pos == 0 || pos == 1 || pos == 2 || pos == 4 || pos == 8)){
                    int stream_pos = (3*error_row) + error_col -3 + (error_row == 3 ? 1 : 0);
                    out[offset + stream_pos] = !out[offset + stream_pos];
                    *numErrors += 1;
                }
            }
        }
    }
    return out_len;
}

int decode_hamming_11(bool *encoded, int len, bool *out, bool* hasDoubleFlip) {
    int numErrors;
    return decode_hamming_11(encoded, len, out, hasDoubleFlip, &numErrors);
}

int main() {
    bool bits[22] = {0,0,1,1,0,0,0,1,1,1,0, 1,1,0,1,0,1,0,0,0,0,0};
    bool *enc = new bool[0];
    int len = encode_hamming_11(&bits[0], 22, enc);


    enc[15] = !enc[15];
    //enc[23] = !enc[23];
    //enc[22] = !enc[22];

    bool *out = new bool[0];
    int numFixes;
    bool hasDoubleFlip;
    len = decode_hamming_11(enc, len, out, &hasDoubleFlip, &numFixes);

    std::cout << "num bits: " << len
              << " | fixes: " << numFixes
              << " | has double flip: " << hasDoubleFlip
              << std::endl;

    for (auto val : bits) {
        std::cout << val << " ";
    }

    std::cout << "  <-- original bits";
    std::cout << std::endl;

    for (int i = 0; i<len; i++) {
        std::cout << out[i] << " ";
    }

    std::cout << "  <-- decoded bits";

    return 1;
}