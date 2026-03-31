vec4 main(const in inputImage in0, const in vec4 channelOrder)
{  
    vec4 pixel = in0();
    vec4 result = vec4(0.0);

    for (int i = 0; i < 4; i++)
    {  
        int channel = int(channelOrder[i]);
        if (channel == 0) result[i] = pixel.r;
        else if (channel == 1) result[i] = pixel.g;
        else if (channel == 2) result[i] = pixel.b;
        else if (channel == 3) result[i] = pixel.a;
        else if (channel == 4) result[i] = pixel.a;
        else if (channel == 5) result[i] = 0.3086 * pixel.r + 0.6094 * pixel.g + 0.0820 * pixel.b;
        else if (channel == 6) result[i] = 0.0;
        else if (channel == 7) result[i] = 1.0;
    }
    return result;
}